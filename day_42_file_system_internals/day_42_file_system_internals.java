import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

public class FileSystemInternalsEnterprise {

    enum FileType {
        FILE,
        DIRECTORY
    }

    enum JournalState {
        PREPARED,
        COMMITTED
    }

    enum InodeAttribute {
        ACCESS,
        MODIFICATION,
        CHANGE
    }

    static final class FileSystemException extends RuntimeException {
        FileSystemException(String message) {
            super(message);
        }
    }

    static final class Superblock {
        final String magic;
        final int blockSize;
        final int totalBlocks;
        final int inodeLimit;
        final int rootInode;
        final int journalCapacity;
        int generation;
        boolean clean;

        Superblock(
                String magic,
                int blockSize,
                int totalBlocks,
                int inodeLimit,
                int rootInode,
                int journalCapacity
        ) {
            this.magic = magic;
            this.blockSize = blockSize;
            this.totalBlocks = totalBlocks;
            this.inodeLimit = inodeLimit;
            this.rootInode = rootInode;
            this.journalCapacity = journalCapacity;
            this.generation = 1;
            this.clean = true;
        }
    }

    static final class Inode {
        final int number;
        final FileType type;
        final int mode;
        final int parent;

        int size;
        int linkCount;
        final List<Integer> directBlocks = new ArrayList<>();
        Integer indirectBlock;
        final List<Integer> indirectEntries = new ArrayList<>();
        final EnumMap<InodeAttribute, Long> timestamps =
                new EnumMap<>(InodeAttribute.class);

        Inode(int number, FileType type, int mode, int parent) {
            this.number = number;
            this.type = type;
            this.mode = mode;
            this.parent = parent;
            this.linkCount = type == FileType.DIRECTORY ? 2 : 1;

            long now = System.currentTimeMillis();
            timestamps.put(InodeAttribute.ACCESS, now);
            timestamps.put(InodeAttribute.MODIFICATION, now);
            timestamps.put(InodeAttribute.CHANGE, now);
        }

        List<Integer> dataBlocks() {
            List<Integer> result = new ArrayList<>(directBlocks);
            result.addAll(indirectEntries);
            return result;
        }
    }

    record DirectoryEntry(String name, int inode) {}

    static final class JournalTransaction {
        final int id;
        final String operation;
        final Map<Integer, Inode> inodeSnapshots;
        final Map<Integer, List<DirectoryEntry>> directorySnapshots;
        final JournalState state;

        JournalTransaction(
                int id,
                String operation,
                Map<Integer, Inode> inodeSnapshots,
                Map<Integer, List<DirectoryEntry>> directorySnapshots
        ) {
            this.id = id;
            this.operation = operation;
            this.inodeSnapshots = inodeSnapshots;
            this.directorySnapshots = directorySnapshots;
            this.state = JournalState.PREPARED;
        }
    }

    interface MergePolicy {
        boolean permits(String operation, Inode inode);
    }

    /*
     * The policy abstraction is deliberately separate from storage mechanics.
     * In an enterprise filesystem service, this allows operational policy to
     * evolve without embedding it into low-level allocation routines.
     */
    static final class RepositoryStoragePolicy implements MergePolicy {
        @Override
        public boolean permits(String operation, Inode inode) {
            if (operation == null || operation.isBlank()) {
                return false;
            }

            if (inode.type == FileType.DIRECTORY && operation.equals("append")) {
                return false;
            }

            return true;
        }
    }

    static final class FileSystemService {
        private static final String MAGIC = "JAVA-ENTERPRISE-FS";
        private static final int DIRECT_LIMIT = 4;

        private final Superblock superblock;
        private final Map<Integer, Inode> inodes = new HashMap<>();
        private final Map<Integer, Map<String, Integer>> directories =
                new HashMap<>();
        private final Set<Integer> allocatedBlocks = new HashSet<>();
        private final Set<Integer> metadataBlocks = new HashSet<>();
        private final Map<Integer, byte[]> disk = new HashMap<>();
        private final List<JournalTransaction> journal = new ArrayList<>();

        private int nextInode = 1;
        private int nextTransaction = 1;
        private boolean mounted;

        FileSystemService(
                int blockSize,
                int totalBlocks,
                int inodeLimit,
                int journalCapacity
        ) {
            if (blockSize <= 0 || totalBlocks < 48) {
                throw new IllegalArgumentException(
                        "Invalid filesystem geometry"
                );
            }

            if (8 + journalCapacity >= totalBlocks) {
                throw new IllegalArgumentException(
                        "Journal leaves insufficient data blocks"
                );
            }

            superblock = new Superblock(
                    MAGIC,
                    blockSize,
                    totalBlocks,
                    inodeLimit,
                    1,
                    journalCapacity
            );

            for (int block = 0; block < 8 + journalCapacity; block++) {
                metadataBlocks.add(block);
                allocatedBlocks.add(block);
                disk.put(block, new byte[blockSize]);
            }

            Inode root = allocateInode(
                    FileType.DIRECTORY,
                    0755,
                    1
            );

            directories.put(
                    root.number,
                    new HashMap<>(
                            Map.of(
                                    ".", root.number,
                                    "..", root.number
                            )
                    )
            );
        }

        void mount() {
            if (mounted) {
                return;
            }

            if (!MAGIC.equals(superblock.magic)) {
                throw new FileSystemException(
                        "Filesystem magic mismatch"
                );
            }

            if (!superblock.clean) {
                recoverJournal();
            }

            verifyConsistency();
            mounted = true;

            System.out.println(
                    "[mount] mounted generation "
                            + superblock.generation
            );
        }

        void unmount() {
            requireMounted();
            verifyConsistency();

            superblock.clean = true;
            mounted = false;

            System.out.println("[mount] clean unmount");
        }

        void simulateCrash() {
            requireMounted();
            superblock.clean = false;
            mounted = false;

            System.out.println("[crash] simulated abrupt shutdown");
        }

        int createDirectory(String path) {
            requireMounted();

            PathTarget target = parentAndName(path);
            ensureName(target.name());

            Map<String, Integer> parentDirectory =
                    directories.get(target.parent());

            if (parentDirectory.containsKey(target.name())) {
                throw new FileSystemException(
                        "Directory entry already exists"
                );
            }

            JournalTransaction transaction =
                    beginTransaction(
                            "mkdir " + path,
                            List.of(target.parent()),
                            List.of(target.parent())
                    );

            Inode inode = allocateInode(
                    FileType.DIRECTORY,
                    0755,
                    target.parent()
            );

            directories.put(
                    inode.number,
                    new HashMap<>(
                            Map.of(
                                    ".", inode.number,
                                    "..", target.parent()
                            )
                    )
            );

            parentDirectory.put(target.name(), inode.number);
            inodes.get(target.parent()).linkCount++;

            commit(transaction);
            return inode.number;
        }

        int createFile(String path) {
            requireMounted();

            PathTarget target = parentAndName(path);
            ensureName(target.name());

            Map<String, Integer> parentDirectory =
                    directories.get(target.parent());

            if (parentDirectory.containsKey(target.name())) {
                throw new FileSystemException(
                        "Directory entry already exists"
                );
            }

            JournalTransaction transaction =
                    beginTransaction(
                            "create " + path,
                            List.of(target.parent()),
                            List.of(target.parent())
                    );

            Inode inode = allocateInode(
                    FileType.FILE,
                    0644,
                    target.parent()
            );

            parentDirectory.put(target.name(), inode.number);
            commit(transaction);

            return inode.number;
        }

        int append(
                String path,
                String content,
                MergePolicy policy
        ) {
            requireMounted();

            int inodeNumber = resolve(path);
            Inode inode = inodes.get(inodeNumber);

            if (!policy.permits("append", inode)) {
                throw new FileSystemException(
                        "Storage policy rejected append"
                );
            }

            if (inode.type != FileType.FILE) {
                throw new FileSystemException(
                        "Only regular files can receive data"
                );
            }

            byte[] payload =
                    content.getBytes(StandardCharsets.UTF_8);

            int offset = inode.size;
            int finalSize = offset + payload.length;
            int requiredBlocks =
                    (finalSize + superblock.blockSize - 1)
                            / superblock.blockSize;

            JournalTransaction transaction =
                    beginTransaction(
                            "append " + path,
                            List.of(inode.number),
                            Collections.emptyList()
                    );

            while (inode.dataBlocks().size() < requiredBlocks) {
                int block = allocateBlock();

                if (inode.directBlocks.size() < DIRECT_LIMIT) {
                    inode.directBlocks.add(block);
                } else {
                    if (inode.indirectBlock == null) {
                        inode.indirectBlock = allocateBlock();
                    }

                    inode.indirectEntries.add(block);
                }
            }

            for (int position = 0;
                 position < payload.length;
                 position++) {

                int absolute = offset + position;
                int logicalBlock =
                        absolute / superblock.blockSize;
                int localOffset =
                        absolute % superblock.blockSize;

                int physical =
                        inode.dataBlocks().get(logicalBlock);

                disk.get(physical)[localOffset] =
                        payload[position];
            }

            inode.size = finalSize;
            touch(inode, InodeAttribute.MODIFICATION);
            touch(inode, InodeAttribute.CHANGE);

            commit(transaction);
            return payload.length;
        }

        String read(String path) {
            requireMounted();

            Inode inode = inodes.get(resolve(path));

            if (inode.type != FileType.FILE) {
                throw new FileSystemException(
                        "Only regular files can be read"
                );
            }

            byte[] result = new byte[inode.size];

            for (int position = 0;
                 position < inode.size;
                 position++) {

                int logicalBlock =
                        position / superblock.blockSize;
                int localOffset =
                        position % superblock.blockSize;

                int physical =
                        inode.dataBlocks().get(logicalBlock);

                result[position] =
                        disk.get(physical)[localOffset];
            }

            touch(inode, InodeAttribute.ACCESS);

            return new String(
                    result,
                    StandardCharsets.UTF_8
            );
        }

        void truncate(String path, int newSize) {
            requireMounted();

            if (newSize < 0) {
                throw new IllegalArgumentException(
                        "Negative file size"
                );
            }

            int inodeNumber = resolve(path);
            Inode inode = inodes.get(inodeNumber);

            if (inode.type != FileType.FILE) {
                throw new FileSystemException(
                        "Only regular files can be truncated"
                );
            }

            JournalTransaction transaction =
                    beginTransaction(
                            "truncate " + path,
                            List.of(inodeNumber),
                            Collections.emptyList()
                    );

            int requiredBlocks =
                    (newSize + superblock.blockSize - 1)
                            / superblock.blockSize;

            while (inode.dataBlocks().size() > requiredBlocks) {
                if (!inode.indirectEntries.isEmpty()) {
                    int block =
                            inode.indirectEntries.remove(
                                    inode.indirectEntries.size() - 1
                            );
                    freeBlock(block);
                } else {
                    int block =
                            inode.directBlocks.remove(
                                    inode.directBlocks.size() - 1
                            );
                    freeBlock(block);
                }
            }

            if (
                    inode.indirectEntries.isEmpty()
                            && inode.indirectBlock != null
            ) {
                freeBlock(inode.indirectBlock);
                inode.indirectBlock = null;
            }

            inode.size = newSize;
            touch(inode, InodeAttribute.MODIFICATION);
            touch(inode, InodeAttribute.CHANGE);

            commit(transaction);
        }

        Optional<Integer> find(String path) {
            try {
                return Optional.of(resolve(path));
            } catch (FileSystemException exception) {
                return Optional.empty();
            }
        }

        void printStorageState(String path) {
            Inode inode = inodes.get(resolve(path));

            System.out.println(
                    "inode=" + inode.number
                            + ", type=" + inode.type
                            + ", size=" + inode.size
                            + ", direct=" + inode.directBlocks
                            + ", indirect="
                            + inode.indirectBlock
                            + ", indirectEntries="
                            + inode.indirectEntries
            );
        }

        String allocationDigest() {
            try {
                MessageDigest digest =
                        MessageDigest.getInstance("SHA-256");

                List<Integer> blocks =
                        new ArrayList<>(allocatedBlocks);
                Collections.sort(blocks);

                for (int block : blocks) {
                    digest.update(
                            (block + ",").getBytes(
                                    StandardCharsets.UTF_8
                            )
                    );
                }

                StringBuilder output = new StringBuilder();

                for (byte value : digest.digest()) {
                    output.append(
                            String.format("%02x", value)
                    );
                }

                return output.toString();
            } catch (NoSuchAlgorithmException exception) {
                throw new IllegalStateException(
                        "SHA-256 is required by the Java runtime",
                        exception
                );
            }
        }

        void verifyConsistency() {
            if (!inodes.containsKey(superblock.rootInode)) {
                throw new FileSystemException(
                        "Root inode is missing"
                );
            }

            Set<Integer> referenced =
                    new HashSet<>(metadataBlocks);

            for (Inode inode : inodes.values()) {
                if (inode.type == FileType.FILE) {
                    int required =
                            (inode.size + superblock.blockSize - 1)
                                    / superblock.blockSize;

                    if (inode.dataBlocks().size() < required) {
                        throw new FileSystemException(
                                "Inode lacks required data blocks"
                        );
                    }
                }

                for (int block : inode.dataBlocks()) {
                    if (!referenced.add(block)) {
                        throw new FileSystemException(
                                "Multiple allocation of block "
                                        + block
                        );
                    }
                }

                if (inode.indirectBlock != null) {
                    if (!referenced.add(inode.indirectBlock)) {
                        throw new FileSystemException(
                                "Indirect block is multiply allocated"
                        );
                    }
                }
            }

            if (!referenced.equals(allocatedBlocks)) {
                throw new FileSystemException(
                        "Allocation map differs from inode references"
                );
            }

            for (Map.Entry<Integer, Map<String, Integer>> directory
                    : directories.entrySet()) {

                if (
                        !directory.getValue().containsKey(".")
                                || !directory.getValue().containsKey("..")
                ) {
                    throw new FileSystemException(
                            "Directory missing dot entries"
                    );
                }

                for (int referencedInode
                        : directory.getValue().values()) {

                    if (!inodes.containsKey(referencedInode)) {
                        throw new FileSystemException(
                                "Dangling directory reference"
                        );
                    }
                }
            }
        }

        private Inode allocateInode(
                FileType type,
                int mode,
                int parent
        ) {
            if (inodes.size() >= superblock.inodeLimit) {
                throw new FileSystemException(
                        "Inode table exhausted"
                );
            }

            Inode inode =
                    new Inode(
                            nextInode++,
                            type,
                            mode,
                            parent
                    );

            inodes.put(inode.number, inode);
            return inode;
        }

        private int allocateBlock() {
            for (int block = 0;
                 block < superblock.totalBlocks;
                 block++) {

                if (!allocatedBlocks.contains(block)) {
                    allocatedBlocks.add(block);
                    disk.put(
                            block,
                            new byte[superblock.blockSize]
                    );
                    return block;
                }
            }

            throw new FileSystemException(
                    "Data block allocation failed"
            );
        }

        private void freeBlock(int block) {
            if (metadataBlocks.contains(block)) {
                throw new FileSystemException(
                        "Metadata block cannot be freed"
                );
            }

            allocatedBlocks.remove(block);
            disk.remove(block);
        }

        private JournalTransaction beginTransaction(
                String operation,
                List<Integer> inodeNumbers,
                List<Integer> directoryNumbers
        ) {
            if (
                    journal.size()
                            >= superblock.journalCapacity
            ) {
                throw new FileSystemException(
                        "Journal capacity reached"
                );
            }

            Map<Integer, Inode> inodeSnapshots =
                    new HashMap<>();

            for (int number : inodeNumbers) {
                inodeSnapshots.put(
                        number,
                        inodes.get(number)
                );
            }

            Map<Integer, List<DirectoryEntry>>
                    directorySnapshots =
                    new HashMap<>();

            for (int number : directoryNumbers) {
                Map<String, Integer> directory =
                        directories.get(number);

                List<DirectoryEntry> entries =
                        new ArrayList<>();

                for (Map.Entry<String, Integer> entry
                        : directory.entrySet()) {

                    entries.add(
                            new DirectoryEntry(
                                    entry.getKey(),
                                    entry.getValue()
                            )
                    );
                }

                directorySnapshots.put(number, entries);
            }

            JournalTransaction transaction =
                    new JournalTransaction(
                            nextTransaction++,
                            operation,
                            inodeSnapshots,
                            directorySnapshots
                    );

            journal.add(transaction);
            superblock.clean = false;

            System.out.println(
                    "[journal] prepare #"
                            + transaction.id
                            + " "
                            + operation
            );

            return transaction;
        }

        private void commit(
                JournalTransaction transaction
        ) {
            superblock.clean = true;
            superblock.generation++;

            journal.remove(transaction);

            System.out.println(
                    "[journal] commit #"
                            + transaction.id
            );
        }

        private void recoverJournal() {
            /*
             * Journal records are the durable intent boundary. A production
             * implementation would persist serialized journal records and
             * replay committed records in sequence-number order.
             */
            journal.clear();
            superblock.clean = true;
            superblock.generation++;

            System.out.println("[journal] recovery completed");
        }

        private int resolve(String path) {
            requireMounted();
            return resolveInternal(path);
        }

        private int resolveInternal(String path) {
            if (!path.startsWith("/")) {
                throw new FileSystemException(
                        "Only absolute paths are supported"
                );
            }

            int current = superblock.rootInode;

            for (String component : path.split("/")) {
                if (component.isBlank() || component.equals(".")) {
                    continue;
                }

                if (component.equals("..")) {
                    current = inodes.get(current).parent;
                    continue;
                }

                Map<String, Integer> directory =
                        directories.get(current);

                if (directory == null) {
                    throw new FileSystemException(
                            "Path component is not a directory"
                    );
                }

                Integer next = directory.get(component);

                if (next == null) {
                    throw new FileSystemException(
                            "Path does not exist: " + path
                    );
                }

                current = next;
            }

            return current;
        }

        private PathTarget parentAndName(String path) {
            if (!path.startsWith("/") || path.equals("/")) {
                throw new FileSystemException(
                        "Invalid path"
                );
            }

            int slash = path.lastIndexOf('/');
            String name = path.substring(slash + 1);
            String parentPath =
                    slash == 0
                            ? "/"
                            : path.substring(0, slash);

            return new PathTarget(
                    resolve(parentPath),
                    name
            );
        }

        private void ensureName(String name) {
            if (
                    name.isBlank()
                            || name.equals(".")
                            || name.equals("..")
                            || name.contains("/")
                            || name.getBytes(
                                    StandardCharsets.UTF_8
                            ).length > 255
            ) {
                throw new FileSystemException(
                        "Invalid directory entry name"
                );
            }
        }

        private void touch(
                Inode inode,
                InodeAttribute attribute
        ) {
            inode.timestamps.put(
                    attribute,
                    System.currentTimeMillis()
            );
        }

        private void requireMounted() {
            if (!mounted) {
                throw new FileSystemException(
                        "Filesystem is not mounted"
                );
            }
        }

        private record PathTarget(
                int parent,
                String name
        ) {}
    }

    public static void main(String[] args) {
        FileSystemService filesystem =
                new FileSystemService(
                        32,
                        96,
                        30,
                        10
                );

        filesystem.mount();

        System.out.println(
                "\n=== Enterprise repository storage model ==="
        );

        filesystem.createDirectory("/repositories");
        filesystem.createDirectory("/repositories/payments");
        filesystem.createDirectory(
                "/repositories/payments/objects"
        );

        filesystem.createFile(
                "/repositories/payments/objects/index"
        );

        filesystem.createFile(
                "/repositories/payments/objects/data"
        );

        RepositoryStoragePolicy policy =
                new RepositoryStoragePolicy();

        filesystem.append(
                "/repositories/payments/objects/index",
                "object-a -> block-group-1\n"
                        + "object-b -> block-group-2\n",
                policy
        );

        filesystem.append(
                "/repositories/payments/objects/data",
                "D".repeat(220),
                policy
        );

        filesystem.printStorageState(
                "/repositories/payments/objects/data"
        );

        System.out.println(
                "Index contents:\n"
                        + filesystem.read(
                                "/repositories/payments/objects/index"
                        )
        );

        System.out.println(
                "Allocation digest: "
                        + filesystem.allocationDigest()
        );

        System.out.println("\n=== File truncation ===");

        filesystem.truncate(
                "/repositories/payments/objects/data",
                48
        );

        filesystem.printStorageState(
                "/repositories/payments/objects/data"
        );

        filesystem.verifyConsistency();

        System.out.println(
                "\n=== Remount ==="
        );

        filesystem.unmount();
        filesystem.mount();

        System.out.println(
                "Post-remount index:\n"
                        + filesystem.read(
                                "/repositories/payments/objects/index"
                        )
        );

        filesystem.verifyConsistency();

        System.out.println(
                "Filesystem consistency verification passed."
        );
    }
}
