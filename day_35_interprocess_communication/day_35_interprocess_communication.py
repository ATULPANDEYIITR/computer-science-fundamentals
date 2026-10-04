#!/usr/bin/env python3
"""
Interprocess Communication: pipes, message queues, shared memory, and sockets.

This self-contained program demonstrates four IPC families using Python's
standard library:

- Pipes: byte streams between related processes.
- Message queues: discrete messages exchanged through a multiprocessing queue.
- Shared memory: multiple processes access the same memory region.
- Sockets: bidirectional communication using an explicit network protocol.

The examples use multiprocessing because it creates genuinely independent
processes rather than merely threads inside one interpreter.
"""

from __future__ import annotations

import json
import multiprocessing as mp
import os
import queue
import socket
import struct
import tempfile
import time
from dataclasses import dataclass
from multiprocessing import shared_memory
from pathlib import Path
from typing import Any


def log(message: str) -> None:
    """Print the process ID so IPC activity can be distinguished."""
    print(f"[pid={os.getpid()}] {message}", flush=True)


# ---------------------------------------------------------------------------
# Pipes
# ---------------------------------------------------------------------------

def pipe_worker(connection: Any) -> None:
    """Receive structured records over a multiprocessing pipe."""
    try:
        while True:
            message = connection.recv()

            if message == {"command": "shutdown"}:
                connection.send({"status": "stopped"})
                break

            if not isinstance(message, dict):
                connection.send({"status": "error", "reason": "message must be a dictionary"})
                continue

            if message.get("command") == "multiply":
                try:
                    left = float(message["left"])
                    right = float(message["right"])
                    connection.send(
                        {
                            "status": "ok",
                            "operation": "multiply",
                            "result": left * right,
                        }
                    )
                except (KeyError, TypeError, ValueError):
                    connection.send(
                        {
                            "status": "error",
                            "reason": "multiply requires numeric left and right values",
                        }
                    )
            else:
                connection.send(
                    {
                        "status": "error",
                        "reason": f"unknown command: {message.get('command')!r}",
                    }
                )
    finally:
        connection.close()


def demonstrate_pipe() -> None:
    """
    A duplex Pipe creates two connection endpoints.

    Unlike a byte-oriented anonymous OS pipe, multiprocessing.Pipe serializes
    Python objects for us. It is therefore useful for demonstrating the
    process-level communication pattern without writing a framing protocol.
    """
    print("\n=== PIPE: point-to-point communication ===")

    parent_connection, child_connection = mp.Pipe(duplex=True)
    worker = mp.Process(target=pipe_worker, args=(child_connection,))
    worker.start()
    child_connection.close()

    try:
        requests = [
            {"command": "multiply", "left": 12, "right": 8},
            {"command": "multiply", "left": 7.5, "right": 4},
            {"command": "unknown"},
        ]

        for request in requests:
            parent_connection.send(request)
            response = parent_connection.recv()
            print(f"request={request} -> response={response}")

        parent_connection.send({"command": "shutdown"})
        print(f"shutdown -> {parent_connection.recv()}")
    finally:
        parent_connection.close()
        worker.join(timeout=3)

        if worker.is_alive():
            worker.terminate()
            worker.join()

        print(f"worker_exit_code={worker.exitcode}")


# ---------------------------------------------------------------------------
# Message queues
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Job:
    """A discrete unit of work placed into a process-safe queue."""

    job_id: int
    operation: str
    value: int


def queue_worker(job_queue: Any, result_queue: Any) -> None:
    """
    Consume independent jobs.

    The queue provides message boundaries, so the receiver does not need to
    parse a byte stream to determine where one message ends.
    """
    while True:
        try:
            job = job_queue.get(timeout=2)
        except queue.Empty:
            result_queue.put({"status": "worker_timeout"})
            return

        if job is None:
            result_queue.put({"status": "worker_stopped"})
            return

        try:
            if job.operation == "square":
                result = job.value * job.value
            elif job.operation == "cube":
                result = job.value ** 3
            else:
                raise ValueError(f"unsupported operation: {job.operation}")

            result_queue.put(
                {
                    "job_id": job.job_id,
                    "status": "completed",
                    "result": result,
                }
            )
        except (TypeError, ValueError, OverflowError) as exc:
            result_queue.put(
                {
                    "job_id": job.job_id,
                    "status": "failed",
                    "error": str(exc),
                }
            )


def demonstrate_message_queue() -> None:
    """
    Demonstrate producer/consumer communication.

    Queues are preferable to a single pipe when several producers or consumers
    need to exchange independent work items and message ordering matters.
    """
    print("\n=== MESSAGE QUEUE: producer/consumer communication ===")

    job_queue: Any = mp.Queue(maxsize=8)
    result_queue: Any = mp.Queue()

    worker = mp.Process(target=queue_worker, args=(job_queue, result_queue))
    worker.start()

    jobs = [
        Job(101, "square", 9),
        Job(102, "cube", 4),
        Job(103, "square", -6),
        Job(104, "invalid", 10),
    ]

    for job in jobs:
        job_queue.put(job)
        print(f"queued job {job.job_id}: {job.operation}({job.value})")

    job_queue.put(None)

    received = 0
    while received < len(jobs):
        result = result_queue.get(timeout=5)
        if result.get("status") in {"completed", "failed"}:
            print(f"result: {result}")
            received += 1

    stopped = result_queue.get(timeout=5)
    print(f"worker lifecycle: {stopped}")

    worker.join(timeout=3)

    if worker.is_alive():
        worker.terminate()
        worker.join()

    job_queue.close()
    result_queue.close()


# ---------------------------------------------------------------------------
# Shared memory
# ---------------------------------------------------------------------------

def shared_memory_worker(
    shm_name: str,
    length: int,
    lock: Any,
    increment: int,
) -> None:
    """
    Modify an integer array stored outside the workers' private address spaces.

    Shared memory provides high-throughput access but removes the isolation
    that makes pipes and queues simple. The lock prevents concurrent
    read-modify-write operations from losing updates.
    """
    shm = shared_memory.SharedMemory(name=shm_name)

    try:
        values = memoryview(shm.buf).cast("q")

        for index in range(length):
            with lock:
                values[index] += increment

        values.release()
    finally:
        shm.close()


def demonstrate_shared_memory() -> None:
    print("\n=== SHARED MEMORY: common memory region ===")

    count = 6
    shm = shared_memory.SharedMemory(create=True, size=count * 8)
    lock = mp.Lock()

    try:
        values = memoryview(shm.buf).cast("q")

        for index in range(count):
            values[index] = index * 10

        print("initial values:", list(values))

        workers = [
            mp.Process(
                target=shared_memory_worker,
                args=(shm.name, count, lock, increment),
            )
            for increment in (1, 10, 100)
        ]

        for worker in workers:
            worker.start()

        for worker in workers:
            worker.join(timeout=5)

        if any(worker.is_alive() for worker in workers):
            for worker in workers:
                if worker.is_alive():
                    worker.terminate()
                    worker.join()

        print("final values:", list(values))

        expected = [index * 10 + 111 for index in range(count)]
        print("expected values:", expected)
        print("correct:", list(values) == expected)

        values.release()
    finally:
        shm.close()
        shm.unlink()


# ---------------------------------------------------------------------------
# Unix domain sockets
# ---------------------------------------------------------------------------

def recv_exact(sock: socket.socket, size: int) -> bytes:
    """
    Receive exactly `size` bytes.

    TCP and Unix stream sockets do not preserve application message
    boundaries. A single recv() may return less data than requested, so the
    protocol must explicitly frame messages.
    """
    chunks: list[bytes] = []
    remaining = size

    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("peer closed the socket before the frame was complete")
        chunks.append(chunk)
        remaining -= len(chunk)

    return b"".join(chunks)


def send_frame(sock: socket.socket, payload: dict[str, Any]) -> None:
    """
    Send a length-prefixed JSON message.

    The four-byte network-order length is framing metadata, not application
    data. Limiting frame size protects the receiver from unbounded allocation.
    """
    encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    if len(encoded) > 1_048_576:
        raise ValueError("payload exceeds the 1 MiB protocol limit")

    header = struct.pack("!I", len(encoded))
    sock.sendall(header + encoded)


def receive_frame(sock: socket.socket) -> dict[str, Any]:
    header = recv_exact(sock, 4)
    (length,) = struct.unpack("!I", header)

    if length > 1_048_576:
        raise ValueError("peer supplied an oversized frame")

    payload = json.loads(recv_exact(sock, length).decode("utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("protocol payload must be a JSON object")

    return payload


def socket_server(socket_path: str) -> None:
    """Serve requests over a local Unix domain stream socket."""
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        try:
            Path(socket_path).unlink()
        except FileNotFoundError:
            pass

        server.bind(socket_path)

        # Restrict the filesystem socket itself. Unix-domain sockets can
        # otherwise become an unintended local IPC attack surface.
        os.chmod(socket_path, 0o600)

        server.listen(4)

        client, _ = server.accept()

        with client:
            while True:
                request = receive_frame(client)

                if request.get("command") == "shutdown":
                    send_frame(client, {"status": "stopped"})
                    break

                if request.get("command") != "stats":
                    send_frame(
                        client,
                        {"status": "error", "reason": "unsupported command"},
                    )
                    continue

                numbers = request.get("numbers")

                if (
                    not isinstance(numbers, list)
                    or not numbers
                    or not all(isinstance(number, (int, float)) for number in numbers)
                ):
                    send_frame(
                        client,
                        {
                            "status": "error",
                            "reason": "numbers must be a non-empty numeric array",
                        },
                    )
                    continue

                total = sum(numbers)
                mean = total / len(numbers)

                send_frame(
                    client,
                    {
                        "status": "ok",
                        "count": len(numbers),
                        "sum": total,
                        "mean": mean,
                        "minimum": min(numbers),
                        "maximum": max(numbers),
                    },
                )
    except (ConnectionError, OSError, ValueError, json.JSONDecodeError) as exc:
        log(f"socket server error: {exc}")
    finally:
        server.close()
        try:
            Path(socket_path).unlink()
        except FileNotFoundError:
            pass


def demonstrate_socket() -> None:
    """
    Demonstrate a local socket service.

    Unix domain sockets use the socket API but avoid TCP/IP routing because
    both endpoints are on the same host. The same framing approach can be
    applied to TCP sockets when communication crosses machine boundaries.
    """
    print("\n=== SOCKET: bidirectional stream communication ===")

    with tempfile.TemporaryDirectory() as temporary_directory:
        socket_path = str(Path(temporary_directory) / "ipc-demo.sock")

        server = mp.Process(target=socket_server, args=(socket_path,))
        server.start()

        deadline = time.monotonic() + 3

        while not Path(socket_path).exists():
            if time.monotonic() >= deadline:
                raise TimeoutError("socket server did not create its endpoint")
            time.sleep(0.01)

        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        try:
            client.settimeout(3)
            client.connect(socket_path)

            send_frame(
                client,
                {"command": "stats", "numbers": [12, 18, 21, 9, 30]},
            )
            print("stats response:", receive_frame(client))

            send_frame(
                client,
                {"command": "stats", "numbers": []},
            )
            print("validation response:", receive_frame(client))

            send_frame(client, {"command": "shutdown"})
            print("shutdown response:", receive_frame(client))
        finally:
            client.close()

        server.join(timeout=3)

        if server.is_alive():
            server.terminate()
            server.join()


# ---------------------------------------------------------------------------
# Comparison and selection
# ---------------------------------------------------------------------------

def compare_ipc_mechanisms() -> None:
    print("\n=== IPC MECHANISM COMPARISON ===")

    comparison = [
        ("Pipe", "stream/endpoint", "small point-to-point exchanges", "serialization or byte protocol"),
        ("Message queue", "discrete messages", "work distribution and producer/consumer systems", "queue capacity and message ordering"),
        ("Shared memory", "shared bytes", "high-throughput local data exchange", "explicit synchronization and ownership"),
        ("Socket", "stream or datagram", "local or network communication", "framing, authentication, and network failures"),
    ]

    for mechanism, abstraction, useful_for, main_risk in comparison:
        print(
            f"{mechanism:15} | abstraction={abstraction:22} | "
            f"use={useful_for:48} | concern={main_risk}"
        )


def demonstrate_failure_modes() -> None:
    """
    Show failures that are characteristic of IPC rather than hiding them.

    A closed pipe reports EOF/connection closure, a queue can time out, shared
    memory requires coordinated cleanup, and sockets can fail between send
    and receive. Production systems must treat IPC as fallible.
    """
    print("\n=== IPC FAILURE HANDLING ===")

    parent, child = mp.Pipe()
    child.close()

    try:
        parent.send({"test": "closed endpoint"})
        parent.recv()
    except (BrokenPipeError, EOFError, OSError) as exc:
        print(f"closed pipe detected: {type(exc).__name__}")
    finally:
        parent.close()

    empty_queue: Any = mp.Queue(maxsize=1)

    try:
        empty_queue.get(timeout=0.05)
    except queue.Empty:
        print("empty queue detected through timeout")
    finally:
        empty_queue.close()


def main() -> None:
    print("Interprocess Communication laboratory")
    print(f"Python process PID: {os.getpid()}")

    demonstrate_pipe()
    demonstrate_message_queue()
    demonstrate_shared_memory()
    demonstrate_socket()
    demonstrate_failure_modes()
    compare_ipc_mechanisms()

    print("\nIPC demonstrations completed.")


if __name__ == "__main__":
    # On Windows, spawn starts a fresh interpreter. Keeping process creation
    # behind this guard prevents recursive child-process creation.
    mp.freeze_support()
    main()
