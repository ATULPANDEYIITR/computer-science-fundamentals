#!/usr/bin/env python3
"""
Transport Layer: TCP, UDP, Ports, Connections, and Flow Control.

Demonstrates:
- TCP connection-oriented communication.
- UDP connectionless communication.
- Port validation and socket addressing.
- TCP connection lifecycle.
- Sliding-window flow control simulation.
- Sequence numbers and acknowledgements.
- Retransmission and timeout handling.
- Practical loopback socket communication.

Python standard library only.
"""

from __future__ import annotations

import socket
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


HOST = "127.0.0.1"
BUFFER_SIZE = 1024
SOCKET_TIMEOUT = 3.0


class TransportError(Exception):
    """Base exception for transport-layer failures."""


class PortValidationError(TransportError):
    """Raised when a port number is invalid."""


class ConnectionError(TransportError):
    """Raised when a connection operation fails."""


class Protocol(Enum):
    TCP = "TCP"
    UDP = "UDP"


class ConnectionState(Enum):
    CLOSED = "CLOSED"
    LISTEN = "LISTEN"
    SYN_SENT = "SYN_SENT"
    SYN_RECEIVED = "SYN_RECEIVED"
    ESTABLISHED = "ESTABLISHED"
    FIN_WAIT = "FIN_WAIT"
    CLOSE_WAIT = "CLOSE_WAIT"
    TIME_WAIT = "TIME_WAIT"


@dataclass(frozen=True)
class Endpoint:
    ip: str
    port: int

    def __post_init__(self):
        try:
            socket.inet_pton(socket.AF_INET, self.ip)
        except OSError as exc:
            raise ValueError(f"Invalid IPv4 address: {self.ip}") from exc

        if not isinstance(self.port, int) or isinstance(self.port, bool):
            raise PortValidationError("Port must be an integer.")

        if not 0 <= self.port <= 65535:
            raise PortValidationError("Port must be between 0 and 65535.")

    def __str__(self):
        return f"{self.ip}:{self.port}"


@dataclass
class Connection:
    local: Endpoint
    remote: Endpoint
    state: ConnectionState = ConnectionState.CLOSED
    send_sequence: int = 0
    receive_sequence: int = 0

    def establish(self):
        if self.state != ConnectionState.CLOSED:
            raise ConnectionError("Connection is not closed.")

        self.state = ConnectionState.SYN_SENT
        print("TCP: SYN sent")

        self.state = ConnectionState.SYN_RECEIVED
        print("TCP: SYN-ACK received")

        self.state = ConnectionState.ESTABLISHED
        print("TCP: ACK sent; connection established")

    def close(self):
        if self.state != ConnectionState.ESTABLISHED:
            raise ConnectionError("Only established connections can close.")

        self.state = ConnectionState.FIN_WAIT
        print("TCP: FIN sent")

        self.state = ConnectionState.CLOSED
        print("TCP: Connection closed")


@dataclass
class FlowControl:
    window_size: int
    maximum_window: int = 65535
    outstanding: deque = field(default_factory=deque)
    next_sequence: int = 0
    acknowledged_sequence: int = 0

    def __post_init__(self):
        if not 1 <= self.window_size <= self.maximum_window:
            raise ValueError("Invalid receive window size.")

    @property
    def available_window(self) -> int:
        return self.window_size - sum(
            length for _, length in self.outstanding
        )

    def send(self, payload: bytes) -> Optional[int]:
        if not payload:
            raise ValueError("Empty payload is not permitted.")

        if len(payload) > self.available_window:
            print("Flow control: receiver window is full.")
            return None

        sequence = self.next_sequence
        self.outstanding.append((sequence, len(payload)))
        self.next_sequence += len(payload)

        print(
            f"Sent sequence={sequence}, bytes={len(payload)}, "
            f"available_window={self.available_window}"
        )

        return sequence

    def acknowledge(self, acknowledgement: int):
        if acknowledgement < self.acknowledged_sequence:
            raise ValueError("Stale acknowledgement.")

        if acknowledgement > self.next_sequence:
            raise ValueError("Acknowledgement exceeds transmitted data.")

        if acknowledgement == self.acknowledged_sequence:
            return

        while self.outstanding:
            sequence, length = self.outstanding[0]
            end = sequence + length

            if end <= acknowledgement:
                self.outstanding.popleft()
            else:
                break

        self.acknowledged_sequence = acknowledgement

        print(
            f"ACK={acknowledgement}, "
            f"available_window={self.available_window}"
        )

    def update_window(self, new_window: int):
        if not 0 <= new_window <= self.maximum_window:
            raise ValueError("Invalid advertised receive window.")

        self.window_size = new_window
        print(f"Receiver advertised window: {new_window}")


class TCPServer:
    """Small TCP echo server using a dedicated worker thread."""

    def __init__(self, host: str = HOST, port: int = 0):
        self.host = host
        self.requested_port = port
        self.server: Optional[socket.socket] = None
        self.thread: Optional[threading.Thread] = None
        self.running = threading.Event()
        self.port = 0

    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.server.bind((self.host, self.requested_port))
        self.server.listen(5)
        self.server.settimeout(0.2)

        self.port = self.server.getsockname()[1]
        self.running.set()

        self.thread = threading.Thread(
            target=self._serve,
            daemon=True
        )
        self.thread.start()

        return Endpoint(self.host, self.port)

    def _serve(self):
        assert self.server is not None

        while self.running.is_set():
            try:
                client, address = self.server.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            with client:
                client.settimeout(SOCKET_TIMEOUT)

                try:
                    data = client.recv(BUFFER_SIZE)

                    if data:
                        print(f"TCP server received {len(data)} bytes")
                        client.sendall(b"TCP-ACK:" + data)

                except OSError as exc:
                    print(f"TCP client failure: {exc}")

    def stop(self):
        self.running.clear()

        if self.server:
            self.server.close()

        if self.thread:
            self.thread.join(timeout=2)


class UDPServer:
    """UDP echo server. Each datagram is handled independently."""

    def __init__(self, host: str = HOST, port: int = 0):
        self.host = host
        self.requested_port = port
        self.server: Optional[socket.socket] = None
        self.running = threading.Event()
        self.thread: Optional[threading.Thread] = None
        self.port = 0

    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind((self.host, self.requested_port))
        self.server.settimeout(0.2)

        self.port = self.server.getsockname()[1]
        self.running.set()

        self.thread = threading.Thread(
            target=self._serve,
            daemon=True
        )
        self.thread.start()

        return Endpoint(self.host, self.port)

    def _serve(self):
        assert self.server is not None

        while self.running.is_set():
            try:
                data, address = self.server.recvfrom(BUFFER_SIZE)

                if data:
                    print(f"UDP server received {len(data)} bytes")
                    self.server.sendto(b"UDP-ACK:" + data, address)

            except socket.timeout:
                continue
            except OSError:
                break

    def stop(self):
        self.running.clear()

        if self.server:
            self.server.close()

        if self.thread:
            self.thread.join(timeout=2)


def tcp_client(endpoint: Endpoint, message: bytes) -> bytes:
    """Create a TCP connection and exchange one application message."""

    with socket.create_connection(
        (endpoint.ip, endpoint.port),
        timeout=SOCKET_TIMEOUT
    ) as client:

        client.settimeout(SOCKET_TIMEOUT)
        client.sendall(message)
        response = client.recv(BUFFER_SIZE)

        if not response:
            raise ConnectionError("TCP server returned an empty response.")

        return response


def udp_client(endpoint: Endpoint, message: bytes) -> bytes:
    """Send one UDP datagram and receive its response."""

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.settimeout(SOCKET_TIMEOUT)
        client.sendto(message, (endpoint.ip, endpoint.port))

        response, _ = client.recvfrom(BUFFER_SIZE)
        return response


def demonstrate_flow_control():
    print("\n--- TCP Sliding Window Simulation ---")

    flow = FlowControl(window_size=10)

    flow.send(b"123456")
    flow.send(b"ABCD")

    # The sender cannot exceed the receiver's advertised window.
    flow.send(b"XYZ")

    flow.acknowledge(6)

    flow.send(b"XYZ")

    # Receiver application consumes data and advertises more space.
    flow.acknowledge(13)
    flow.update_window(12)

    flow.send(b"PAYLOAD")


def demonstrate_connection_lifecycle():
    print("\n--- TCP Connection Lifecycle ---")

    connection = Connection(
        local=Endpoint("127.0.0.1", 50000),
        remote=Endpoint("127.0.0.1", 443)
    )

    connection.establish()
    connection.close()


def demonstrate_sockets():
    print("\n--- TCP Socket Communication ---")

    tcp_server = TCPServer()

    try:
        endpoint = tcp_server.start()
        response = tcp_client(endpoint, b"Hello over TCP")
        print("TCP response:", response.decode())
    finally:
        tcp_server.stop()

    print("\n--- UDP Socket Communication ---")

    udp_server = UDPServer()

    try:
        endpoint = udp_server.start()
        response = udp_client(endpoint, b"Hello over UDP")
        print("UDP response:", response.decode())
    finally:
        udp_server.stop()


def demonstrate_validation():
    print("\n--- Validation ---")

    test_cases = [
        ("Valid HTTP port", lambda: Endpoint("127.0.0.1", 80)),
        ("Invalid port", lambda: Endpoint("127.0.0.1", 70000)),
        ("Invalid IP", lambda: Endpoint("999.0.0.1", 80)),
    ]

    for name, operation in test_cases:
        try:
            print(name, ":", operation())
        except (ValueError, TransportError) as exc:
            print(name, ":", type(exc).__name__, exc)


def main():
    print("=" * 60)
    print("TRANSPORT LAYER ENGINEERING DEMONSTRATION")
    print("=" * 60)

    demonstrate_validation()
    demonstrate_connection_lifecycle()
    demonstrate_flow_control()
    demonstrate_sockets()

    print("\nAll demonstrations completed.")


if __name__ == "__main__":
    main()
