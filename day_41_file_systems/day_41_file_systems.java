import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.nio.file.attribute.*;
import java.time.Instant;
import java.util.*;
import java.util.stream.Stream;

public class FileSystemEnterpriseDemo {

    enum AccessRight {
        READ,
        WRITE,
        EXECUTE
    }

    enum ResourceType {
        FILE,
        DIRECTORY,
        SYMBOLIC_LINK
    }

    record FileMetadata(
            Path path,
            ResourceType type,
            long size,
            Instant modified,
            Set<PosixFilePermission> permissions
    ) {}

    static final class FileSystemService {
        private final Path root;

        FileSystemService(Path root) throws IOException {
            this.root = root.toAbsolutePath().normalize();
            Files.createDirectories(root);
        }

        Path root() {
            return root;
        }

        Path resolveInsideRoot(String relative) {
            Path candidate = root.resolve(relative).normalize();

            if (!candidate.startsWith(root)) {
                throw new SecurityException(
                        "Path escapes approved filesystem root: " + relative
                );
            }

            return candidate;
        }

        void createDirectory(String relative) throws IOException {
            Files.createDirectories(resolveInsideRoot(relative));
        }

        void writeText(String relative, String content) throws IOException {
            Path target = resolveInsideRoot(relative);
            Files.createDirectories(target.getParent());

            Files.writeString(
                    target,
                    content,
                    StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE,
                    StandardOpenOption.TRUNCATE_EXISTING
            );
        }

        String readText(String relative) throws IOException {
            return Files.readString(
                    resolveInsideRoot(relative),
                    StandardCharsets.UTF_8
            );
        }

        FileMetadata metadata(String relative) throws IOException {
            Path target = resolveInsideRoot(relative);
            BasicFileAttributes basic = Files.readAttributes(
                    target,
                    BasicFileAttributes.class,
                    LinkOption.NOFOLLOW_LINKS
            );

            ResourceType type;

            if (basic.isSymbolicLink()) {
                type = ResourceType.SYMBOLIC_LINK;
            } else if (basic.isDirectory()) {
                type = ResourceType.DIRECTORY;
            } else {
                type = ResourceType.FILE;
            }

            Set<PosixFilePermission> permissions =
                    readPosixPermissions(target);

            return new FileMetadata(
                    target,
                    type,
                    basic.size(),
                    basic.lastModifiedTime().toInstant(),
                    permissions
            );
        }

        private Set<PosixFilePermission> readPosixPermissions(Path target) {
            try {
                return Files.getPosixFilePermissions(
                        target,
                        LinkOption.NOFOLLOW_LINKS
                );
            } catch (UnsupportedOperationException | IOException error) {
                return Collections.emptySet();
            }
        }

        boolean hasPermission(
                FileMetadata metadata,
                AccessRight right
        ) {
            if (metadata.permissions().isEmpty()) {
                // Windows and other non-POSIX providers may not expose
                // POSIX permission sets, so Java cannot infer equivalent
                // access semantics from this metadata alone.
                return true;
            }

            return switch (right) {
                case READ ->
                        metadata.permissions().contains(
                                PosixFilePermission.OWNER_READ
                        );
                case WRITE ->
                        metadata.permissions().contains(
                                PosixFilePermission.OWNER_WRITE
                        );
                case EXECUTE ->
                        metadata.permissions().contains(
                                PosixFilePermission.OWNER_EXECUTE
                        );
            };
        }

        List<FileMetadata> inventory() throws IOException {
            List<FileMetadata> result = new ArrayList<>();

            try (Stream<Path> paths = Files.walk(root)) {
                paths.filter(path -> !path.equals(root))
                     .forEach(path -> {
                         try {
                             BasicFileAttributes basic =
                                     Files.readAttributes(
                                             path,
                                             BasicFileAttributes.class,
                                             LinkOption.NOFOLLOW_LINKS
                                     );

                             ResourceType type =
                                     basic.isSymbolicLink()
                                             ? ResourceType.SYMBOLIC_LINK
                                             : basic.isDirectory()
                                             ? ResourceType.DIRECTORY
                                             : ResourceType.FILE;

                             result.add(new FileMetadata(
                                     path,
                                     type,
                                     basic.size(),
                                     basic.lastModifiedTime().toInstant(),
                                     readPosixPermissions(path)
                             ));
                         } catch (IOException error) {
                             throw new UncheckedIOException(error);
                         }
                     });
            }

            result.sort(
                    Comparator.comparing(
                            metadata -> metadata.path().toString()
                    )
            );

            return result;
        }

        void copyForBackup(String sourceRelative, String backupRelative)
                throws IOException {
            Path source = resolveInsideRoot(sourceRelative);
            Path backup = resolveInsideRoot(backupRelative);

            if (!Files.isRegularFile(source, LinkOption.NOFOLLOW_LINKS)) {
                throw new IllegalArgumentException(
                        "Backup source must be a regular file."
                );
            }

            Files.createDirectories(backup.getParent());

            Files.copy(
                    source,
                    backup,
                    StandardCopyOption.REPLACE_EXISTING,
                    StandardCopyOption.COPY_ATTRIBUTES
            );
        }

        void atomicTextUpdate(String relative, String content)
                throws IOException {
            Path destination = resolveInsideRoot(relative);
            Path temporary = destination.resolveSibling(
                    destination.getFileName() + ".tmp"
            );

            Files.createDirectories(destination.getParent());

            Files.writeString(
                    temporary,
                    content,
                    StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE,
                    StandardOpenOption.TRUNCATE_EXISTING
            );

            try {
                Files.move(
                        temporary,
                        destination,
                        StandardCopyOption.ATOMIC_MOVE,
                        StandardCopyOption.REPLACE_EXISTING
                );
            } catch (AtomicMoveNotSupportedException error) {
                Files.move(
                        temporary,
                        destination,
                        StandardCopyOption.REPLACE_EXISTING
                );
            }
        }

        void deleteSafely(String relative) throws IOException {
            Path target = resolveInsideRoot(relative);

            if (target.equals(root)) {
                throw new SecurityException(
                        "Refusing to delete the filesystem root."
                );
            }

            if (Files.isDirectory(
                    target,
                    LinkOption.NOFOLLOW_LINKS
            )) {
                try (Stream<Path> paths = Files.walk(target)) {
                    paths.sorted(Comparator.reverseOrder())
                         .forEach(path -> {
                             try {
                                 Files.deleteIfExists(path);
                             } catch (IOException error) {
                                 throw new UncheckedIOException(error);
                             }
                         });
                }
            } else {
                Files.deleteIfExists(target);
            }
        }
    }

    static void printMetadata(FileMetadata metadata) {
        System.out.println("\nMetadata");
        System.out.println("Path: " + metadata.path());
        System.out.println("Type: " + metadata.type());
        System.out.println("Size: " + metadata.size());
        System.out.println("Modified: " + metadata.modified());
        System.out.println("POSIX permissions: " + metadata.permissions());
    }

    static void printInventory(
            FileSystemService service
    ) throws IOException {
        System.out.println("\nFilesystem inventory");

        for (FileMetadata metadata : service.inventory()) {
            System.out.printf(
                    "%-45s %-15s %10d bytes%n",
                    service.root().relativize(metadata.path()),
                    metadata.type(),
                    metadata.size()
            );
        }
    }

    public static void main(String[] args) {
        Path workspace = null;

        try {
            workspace = Files.createTempDirectory("enterprise-filesystem-");
            FileSystemService service = new FileSystemService(workspace);

            service.createDirectory("application/data");
            service.createDirectory("application/logs");
            service.createDirectory("application/config");

            service.writeText(
                    "application/config/application.properties",
                    "environment=production\n"
                            + "audit=true\n"
                            + "maxFileSize=10485760\n"
            );

            service.writeText(
                    "application/data/customer-records.csv",
                    "customer_id,status\n"
                            + "C1001,active\n"
                            + "C1002,review\n"
            );

            service.writeText(
                    "application/logs/application.log",
                    "2026-10-11 INFO application started\n"
            );

            FileMetadata config = service.metadata(
                    "application/config/application.properties"
            );

            printMetadata(config);

            System.out.println(
                    "Owner read allowed: "
                            + service.hasPermission(
                                    config,
                                    AccessRight.READ
                            )
            );

            System.out.println(
                    "Owner write allowed: "
                            + service.hasPermission(
                                    config,
                                    AccessRight.WRITE
                            )
            );

            service.copyForBackup(
                    "application/config/application.properties",
                    "application/config/application.properties.bak"
            );

            service.atomicTextUpdate(
                    "application/config/application.properties",
                    "environment=production\n"
                            + "audit=true\n"
                            + "maxFileSize=20971520\n"
            );

            System.out.println("\nUpdated configuration:");
            System.out.print(
                    service.readText(
                            "application/config/application.properties"
                    )
            );

            printInventory(service);

            try {
                service.resolveInsideRoot("../../outside.txt");
                throw new AssertionError(
                        "Path traversal should have been rejected."
                );
            } catch (SecurityException expected) {
                System.out.println(
                        "\nPath traversal rejected: "
                                + expected.getMessage()
                );
            }

            service.deleteSafely("application/logs");
            System.out.println(
                    "\nApplication logs removed safely."
            );

        } catch (IOException | UncheckedIOException error) {
            System.err.println(
                    "Filesystem operation failed: "
                            + error.getMessage()
            );
            System.exit(1);
        } finally {
            if (workspace != null) {
                try (Stream<Path> paths = Files.walk(workspace)) {
                    paths.sorted(Comparator.reverseOrder())
                         .forEach(path -> {
                             try {
                                 Files.deleteIfExists(path);
                             } catch (IOException error) {
                                 System.err.println(
                                         "Cleanup failed for "
                                                 + path + ": "
                                                 + error.getMessage()
                                 );
                             }
                         });
                } catch (IOException error) {
                    System.err.println(
                            "Workspace cleanup failed: "
                                    + error.getMessage()
                    );
                }
            }
        }
    }
}
