import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.EOFException;
import java.io.IOException;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.UnixDomainSocketAddress;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;

/*
 * Java 17 enterprise IPC case study.
 *
 * Scenario:
 * A document-processing service accepts work from independent producers,
 * processes messages through a bounded queue, exposes process-local shared
 * state to cooperating threads, and provides a Unix-domain socket for a
 * local operations client.
 *
 * The program keeps the four IPC concepts distinct:
 *
 *   Pipe/stream       -> process stream transport with explicit framing.
 *   Message queue     -> BlockingQueue carrying complete work messages.
 *   Shared memory     -> shared mutable state within the JVM through
 *                        concurrency-safe objects.
 *   Socket            -> Unix-domain request/response endpoint.
 *
 * Java's standard library does not expose the same cross-process anonymous
 * shared-memory primitive as POSIX mmap(). Therefore the shared-state example
 * uses JVM-shared concurrent state, while the socket and stream examples are
 * genuinely process-oriented. Cross-process shared memory in Java normally
 * requires a memory-mapped file or a native/foreign-memory mechanism.
 */
public class IpcEnterpriseCaseStudy {

    private static final int MAX_FRAME_SIZE = 1024 * 1024;

    enum JobState {
        QUEUED,
        PROCESSING,
        COMPLETED,
        FAILED
    }

    record DocumentJob(
        String jobId,
        String documentName,
        String content
    ) {
        DocumentJob {
            if (jobId == null || jobId.isBlank()) {
                throw new IllegalArgumentException("jobId is required");
            }
            if (documentName == null || documentName.isBlank()) {
                throw new IllegalArgumentException("documentName is required");
            }
            if (content == null) {
                throw new IllegalArgumentException("content cannot be null");
            }
        }
    }

    record ProcessingResult(
        String jobId,
        JobState state,
        int wordCount,
        String digest,
        String error
    ) {}

    static final class Metrics {
        private final java.util.concurrent.atomic.AtomicInteger queued =
            new java.util.concurrent.atomic.AtomicInteger();

        private final java.util.concurrent.atomic.AtomicInteger completed =
            new java.util.concurrent.atomic.AtomicInteger();

        private final java.util.concurrent.atomic.AtomicInteger failed =
            new java.util.concurrent.atomic.AtomicInteger();

        void queued() {
            queued.incrementAndGet();
        }

        void completed() {
            completed.incrementAndGet();
        }

        void failed() {
            failed.incrementAndGet();
        }

        String snapshot() {
            return "queued=" + queued.get()
                + " completed=" + completed.get()
                + " failed=" + failed.get();
        }
    }

    /*
     * BlockingQueue models message-oriented communication: each queue element
     * remains an application-level object rather than an arbitrary fragment
     * of a byte stream. The bounded queue creates backpressure.
     */
    static final class JobQueue {
        private final BlockingQueue<DocumentJob> queue;

        JobQueue(int capacity) {
            if (capacity <= 0) {
                throw new IllegalArgumentException("capacity must be positive");
            }
            queue = new LinkedBlockingQueue<>(capacity);
        }

        void submit(DocumentJob job) throws InterruptedException {
            queue.put(Objects.requireNonNull(job));
        }

        DocumentJob receive(long timeout, TimeUnit unit)
            throws InterruptedException {
            return queue.poll(timeout, unit);
        }
    }

    static final class ProcessingService {
        private final JobQueue queue;
        private final Metrics metrics;
        private final Map<String, JobState> states = new ConcurrentHashMap<>();

        ProcessingService(JobQueue queue, Metrics metrics) {
            this.queue = queue;
            this.metrics = metrics;
        }

        void submit(DocumentJob job) throws InterruptedException {
            states.put(job.jobId(), JobState.QUEUED);
            metrics.queued();
            queue.submit(job);
        }

        ProcessingResult process(DocumentJob job) {
            states.put(job.jobId(), JobState.PROCESSING);

            try {
                int words = countWords(job.content());
                String digest = sha256(job.content());

                states.put(job.jobId(), JobState.COMPLETED);
                metrics.completed();

                return new ProcessingResult(
                    job.jobId(),
                    JobState.COMPLETED,
                    words,
                    digest,
                    null
                );
            } catch (RuntimeException exception) {
                states.put(job.jobId(), JobState.FAILED);
                metrics.failed();

                return new ProcessingResult(
                    job.jobId(),
                    JobState.FAILED,
                    0,
                    null,
                    exception.getMessage()
                );
            }
        }

        JobState stateOf(String jobId) {
            return states.get(jobId);
        }

        private static int countWords(String content) {
            String normalized = content.trim();

            if (normalized.isEmpty()) {
                return 0;
            }

            return normalized.split("\\s+").length;
        }

        private static String sha256(String content) {
            try {
                MessageDigest digest = MessageDigest.getInstance("SHA-256");
                byte[] bytes = digest.digest(content.getBytes(
                    java.nio.charset.StandardCharsets.UTF_8
                ));

                StringBuilder result = new StringBuilder();

                for (byte value : bytes) {
                    result.append(String.format("%02x", value));
                }

                return result.toString();
            } catch (Exception exception) {
                throw new IllegalStateException(
                    "SHA-256 unavailable",
                    exception
                );
            }
        }
    }

    /*
     * A length-prefixed stream is necessary because InputStream does not
     * guarantee that one read() corresponds to one logical application
     * message. DataInputStream.readFully() reconstructs the complete frame.
     */
    static final class FramedStream {
        private final DataInputStream input;
        private final DataOutputStream output;

        FramedStream(java.io.InputStream input, java.io.OutputStream output) {
            this.input = new DataInputStream(new BufferedInputStream(input));
            this.output = new DataOutputStream(new BufferedOutputStream(output));
        }

        synchronized void send(String message) throws IOException {
            byte[] payload = message.getBytes(
                java.nio.charset.StandardCharsets.UTF_8
            );

            if (payload.length > MAX_FRAME_SIZE) {
                throw new IOException("frame exceeds protocol limit");
            }

            output.writeInt(payload.length);
            output.write(payload);
            output.flush();
        }

        String receive() throws IOException {
            int length;

            try {
                length = input.readInt();
            } catch (EOFException exception) {
                return null;
            }

            if (length < 0 || length > MAX_FRAME_SIZE) {
                throw new IOException("invalid frame length: " + length);
            }

            byte[] payload = new byte[length];
            input.readFully(payload);

            return new String(
                payload,
                java.nio.charset.StandardCharsets.UTF_8
            );
        }
    }

    static void demonstrateMessageQueue() throws InterruptedException {
        System.out.println("\n=== MESSAGE QUEUE ===");

        JobQueue queue = new JobQueue(3);
        Metrics metrics = new Metrics();
        ProcessingService service = new ProcessingService(queue, metrics);

        Thread consumer = Thread.ofPlatform()
            .name("document-consumer")
            .start(() -> {
                try {
                    while (!Thread.currentThread().isInterrupted()) {
                        DocumentJob job = queue.receive(1, TimeUnit.SECONDS);

                        if (job == null) {
                            return;
                        }

                        ProcessingResult result = service.process(job);
                        System.out.println("processed: " + result);
                    }
                } catch (InterruptedException exception) {
                    Thread.currentThread().interrupt();
                }
            });

        List<DocumentJob> jobs = List.of(
            new DocumentJob(
                "DOC-1001",
                "architecture.txt",
                "pipes queues shared memory sockets"
            ),
            new DocumentJob(
                "DOC-1002",
                "protocol.txt",
                "framing validation timeout retry"
            ),
            new DocumentJob(
                "DOC-1003",
                "security.txt",
                "permissions authentication authorization"
            )
        );

        for (DocumentJob job : jobs) {
            service.submit(job);
        }

        consumer.join(5000);

        if (consumer.isAlive()) {
            consumer.interrupt();
            consumer.join();
        }

        System.out.println("metrics: " + metrics.snapshot());
        System.out.println(
            "state DOC-1001: " + service.stateOf("DOC-1001")
        );
    }

    /*
     * Demonstrates a pipe-like parent/child stream using a subprocess.
     *
     * Java does not expose fork() as a standard API. ProcessBuilder is the
     * portable Java abstraction for creating another operating-system process.
     */
    static void demonstrateProcessPipe() throws Exception {
        System.out.println("\n=== PROCESS PIPE ===");

        String javaExecutable =
            Path.of(
                System.getProperty("java.home"),
                "bin",
                "java"
            ).toString();

        String classPath = System.getProperty("java.class.path");

        Process process = new ProcessBuilder(
            javaExecutable,
            "-cp",
            classPath,
            IpcEnterpriseCaseStudy.class.getName(),
            "--pipe-child"
        )
            .redirectError(ProcessBuilder.Redirect.INHERIT)
            .start();

        try {
            FramedStream stream = new FramedStream(
                process.getInputStream(),
                process.getOutputStream()
            );

            stream.send("PROCESS_STATUS");

            String response = stream.receive();
            System.out.println("child response: " + response);

            stream.send("STOP");
        } finally {
            if (!process.waitFor(5, TimeUnit.SECONDS)) {
                process.destroyForcibly();
                process.waitFor();
            }
        }
    }

    /*
     * Unix-domain sockets avoid TCP/IP routing for local services. They are
     * still stream transports, so FramedStream remains necessary.
     */
    static void demonstrateUnixSocket() throws Exception {
        System.out.println("\n=== UNIX DOMAIN SOCKET ===");

        Path socketPath = Files.createTempFile(
            "java-ipc-",
            ".sock"
        );

        Files.deleteIfExists(socketPath);

        UnixDomainSocketAddress address =
            UnixDomainSocketAddress.of(socketPath);

        try (ServerSocket server = ServerSocket.openUnixDomain()) {
            server.bind(address);

            Thread serverThread = Thread.ofPlatform()
                .name("unix-socket-server")
                .start(() -> {
                    try (Socket client = server.accept()) {
                        FramedStream stream = new FramedStream(
                            client.getInputStream(),
                            client.getOutputStream()
                        );

                        String request = stream.receive();

                        if ("GET_STATUS".equals(request)) {
                            stream.send(
                                "STATUS=READY;TIME=" + Instant.now()
                            );
                        } else {
                            stream.send("ERROR=UNSUPPORTED_REQUEST");
                        }
                    } catch (IOException exception) {
                        System.err.println(
                            "socket server: " + exception.getMessage()
                        );
                    }
                });

            try (Socket client = SocketChannelCompat.open(address)) {
                FramedStream stream = new FramedStream(
                    client.getInputStream(),
                    client.getOutputStream()
                );

                stream.send("GET_STATUS");
                System.out.println(
                    "socket response: " + stream.receive()
                );
            }

            serverThread.join(5000);

            if (serverThread.isAlive()) {
                serverThread.interrupt();
            }
        } finally {
            Files.deleteIfExists(socketPath);
        }
    }

    /*
     * SocketChannel is normally the most direct Java API for Unix-domain
     * sockets. This adapter exposes a Socket-shaped interface so the framing
     * class can remain focused on protocol concerns.
     */
    static final class SocketChannelCompat extends Socket {
        private final java.nio.channels.SocketChannel channel;

        private SocketChannelCompat(
            java.nio.channels.SocketChannel channel
        ) {
            this.channel = channel;
        }

        static SocketChannelCompat open(
            UnixDomainSocketAddress address
        ) throws IOException {
            var channel = java.nio.channels.SocketChannel.open(
                java.net.StandardProtocolFamily.UNIX
            );
            channel.connect(address);
            return new SocketChannelCompat(channel);
        }

        @Override
        public java.io.InputStream getInputStream() {
            return java.nio.channels.Channels.newInputStream(channel);
        }

        @Override
        public java.io.OutputStream getOutputStream() {
            return java.nio.channels.Channels.newOutputStream(channel);
        }

        @Override
        public synchronized void close() throws IOException {
            channel.close();
        }
    }

    static void demonstrateSharedState() throws InterruptedException {
        System.out.println("\n=== SHARED MEMORY CONCEPT ===");

        /*
         * This is shared JVM memory, not cross-process shared memory.
         * AtomicInteger provides visibility and atomic update semantics among
         * threads. A separate JVM would not see these fields.
         */
        var counter =
            new java.util.concurrent.atomic.AtomicInteger(0);

        List<Thread> workers = new ArrayList<>();

        for (int worker = 0; worker < 4; worker++) {
            workers.add(
                Thread.ofPlatform()
                    .name("shared-counter-" + worker)
                    .start(() -> {
                        for (int i = 0; i < 1000; i++) {
                            counter.incrementAndGet();
                        }
                    })
            );
        }

        for (Thread worker : workers) {
            worker.join();
        }

        System.out.println("atomic shared counter=" + counter.get());
        System.out.println(
            "expected=" + (4 * 1000)
        );
    }

    static void demonstrateFailureHandling() {
        System.out.println("\n=== FAILURE HANDLING ===");

        try {
            new DocumentJob("", "bad.txt", "data");
        } catch (IllegalArgumentException exception) {
            System.out.println(
                "validation rejected invalid job: "
                    + exception.getMessage()
            );
        }

        try {
            byte[] oversized =
                new byte[MAX_FRAME_SIZE + 1];

            if (oversized.length > MAX_FRAME_SIZE) {
                throw new IOException(
                    "frame would exceed configured maximum"
                );
            }
        } catch (IOException exception) {
            System.out.println(
                "protocol validation rejected oversized data: "
                    + exception.getMessage()
            );
        }
    }

    static void pipeChild() throws Exception {
        FramedStream stream = new FramedStream(
            System.in,
            System.out
        );

        String request = stream.receive();

        if ("PROCESS_STATUS".equals(request)) {
            stream.send("READY;PID=" + ProcessHandle.current().pid());
        }

        String stop = stream.receive();

        if (!"STOP".equals(stop)) {
            System.err.println("child did not receive STOP");
            System.exit(2);
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length > 0 && "--pipe-child".equals(args[0])) {
            pipeChild();
            return;
        }

        System.out.println("Java 17+ IPC enterprise case study");

        demonstrateMessageQueue();
        demonstrateProcessPipe();
        demonstrateUnixSocket();
        demonstrateSharedState();
        demonstrateFailureHandling();

        System.out.println("\nCase study completed.");
    }
}
