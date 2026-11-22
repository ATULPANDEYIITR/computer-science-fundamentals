#!/usr/bin/env python3
"""
TCP/IP Model: Internet Layer Architecture and Protocol Interaction

Demonstrates:
- TCP/IP four-layer architecture
- Encapsulation and decapsulation
- Application, Transport, Internet, and Network Access layers
- IPv4 addressing and subnet validation
- TCP and UDP transport behavior
- TCP three-way handshake
- IP routing and packet forwarding
- Port and protocol validation
- Packet fragmentation concepts
- Checksum calculation
- Network troubleshooting and failure handling

Python 3.10+
Uses only the Python standard library.
"""

from __future__ import annotations

import ipaddress
import socket
import struct
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ============================================================
# 1. TCP/IP ARCHITECTURE
# ============================================================

class Layer(Enum):
    APPLICATION = 4
    TRANSPORT = 3
    INTERNET = 2
    NETWORK_ACCESS = 1


class Protocol(Enum):
    HTTP = "HTTP"
    HTTPS = "HTTPS"
    DNS = "DNS"
    DHCP = "DHCP"
    TCP = "TCP"
    UDP = "UDP"
    ICMP = "ICMP"
    IP = "IP"
    ETHERNET = "ETHERNET"


class NetworkError(Exception):
    """Base exception for network simulation errors."""


class ValidationError(NetworkError):
    pass


class RoutingError(NetworkError):
    pass


class ConnectionError(NetworkError):
    pass


@dataclass(frozen=True)
class LayerDefinition:
    layer: Layer
    name: str
    responsibilities: tuple[str, ...]


TCP_IP_LAYERS = (
    LayerDefinition(
        Layer.APPLICATION,
        "Application",
        ("Application services", "Data formatting", "Application protocols")
    ),
    LayerDefinition(
        Layer.TRANSPORT,
        "Transport",
        ("End-to-end communication", "Ports", "Segmentation", "Reliability")
    ),
    LayerDefinition(
        Layer.INTERNET,
        "Internet",
        ("Logical addressing", "Routing", "Packet forwarding")
    ),
    LayerDefinition(
        Layer.NETWORK_ACCESS,
        "Network Access",
        ("Framing", "MAC addressing", "Physical transmission")
    ),
)


def display_architecture() -> None:
    print("\nTCP/IP FOUR-LAYER ARCHITECTURE")

    for definition in TCP_IP_LAYERS:
        print(f"\n{definition.layer.value}. {definition.name}")

        for responsibility in definition.responsibilities:
            print(f"   - {responsibility}")


# ============================================================
# 2. IP ADDRESSING AND VALIDATION
# ============================================================

@dataclass(frozen=True)
class IPv4Address:
    address: str

    def __post_init__(self) -> None:
        try:
            parsed = ipaddress.ip_address(self.address)

            if not isinstance(parsed, ipaddress.IPv4Address):
                raise ValidationError("Only IPv4 addresses are supported.")

        except ValueError as exc:
            raise ValidationError(
                f"Invalid IPv4 address: {self.address}"
            ) from exc

    def as_integer(self) -> int:
        return int(ipaddress.IPv4Address(self.address))

    def is_private(self) -> bool:
        return ipaddress.ip_address(self.address).is_private


@dataclass(frozen=True)
class IPv4Network:
    network: ipaddress.IPv4Network

    @classmethod
    def create(cls, cidr: str) -> IPv4Network:
        try:
            network = ipaddress.ip_network(cidr, strict=False)

            if not isinstance(network, ipaddress.IPv4Network):
                raise ValidationError("IPv4 network required.")

            return cls(network)

        except ValueError as exc:
            raise ValidationError(
                f"Invalid network: {cidr}"
            ) from exc

    def contains(self, address: str) -> bool:
        return ipaddress.ip_address(address) in self.network

    def broadcast_address(self) -> str:
        return str(self.network.broadcast_address)

    def usable_hosts(self) -> int:
        return self.network.num_addresses - 2


# ============================================================
# 3. APPLICATION LAYER
# ============================================================

@dataclass
class ApplicationData:
    protocol: Protocol
    payload: bytes

    @classmethod
    def from_text(
        cls,
        protocol: Protocol,
        text: str
    ) -> ApplicationData:
        if protocol not in {
            Protocol.HTTP,
            Protocol.HTTPS,
            Protocol.DNS,
            Protocol.DHCP
        }:
            raise ValidationError(
                "Unsupported application protocol."
            )

        if not text:
            raise ValidationError("Application data cannot be empty.")

        return cls(protocol, text.encode("utf-8"))


# ============================================================
# 4. TRANSPORT LAYER
# ============================================================

class TCPState(Enum):
    CLOSED = "CLOSED"
    LISTEN = "LISTEN"
    SYN_SENT = "SYN_SENT"
    SYN_RECEIVED = "SYN_RECEIVED"
    ESTABLISHED = "ESTABLISHED"
    FIN_WAIT = "FIN_WAIT"
    TIME_WAIT = "TIME_WAIT"


@dataclass
class TCPConnection:
    source_port: int
    destination_port: int
    state: TCPState = TCPState.CLOSED
    sequence_number: int = 1000
    acknowledgment_number: int = 0

    def __post_init__(self) -> None:
        for port in (self.source_port, self.destination_port):
            if not 1 <= port <= 65535:
                raise ValidationError(f"Invalid TCP port: {port}")

    def connect(self) -> list[str]:
        if self.state != TCPState.CLOSED:
            raise ConnectionError("Connection is not closed.")

        events = []

        self.state = TCPState.SYN_SENT
        events.append("Client sends SYN")

        self.state = TCPState.SYN_RECEIVED
        self.acknowledgment_number = self.sequence_number + 1
        events.append("Server responds with SYN-ACK")

        self.state = TCPState.ESTABLISHED
        events.append("Client sends ACK")

        return events

    def close(self) -> list[str]:
        if self.state != TCPState.ESTABLISHED:
            raise ConnectionError(
                "Only established connections can be closed."
            )

        self.state = TCPState.FIN_WAIT
        events = ["FIN sent", "ACK received", "FIN received", "ACK sent"]

        self.state = TCPState.TIME_WAIT
        events.append("Connection enters TIME_WAIT")

        self.state = TCPState.CLOSED
        events.append("Connection closed")

        return events


@dataclass
class UDPDatagram:
    source_port: int
    destination_port: int
    payload: bytes

    def __post_init__(self) -> None:
        for port in (self.source_port, self.destination_port):
            if not 1 <= port <= 65535:
                raise ValidationError("UDP ports must be 1-65535.")

        if len(self.payload) > 65507:
            raise ValidationError("UDP payload exceeds IPv4 limit.")


@dataclass
class TCPSegment:
    source_port: int
    destination_port: int
    sequence_number: int
    acknowledgment_number: int
    flags: tuple[str, ...]
    payload: bytes

    def __post_init__(self) -> None:
        for port in (self.source_port, self.destination_port):
            if not 1 <= port <= 65535:
                raise ValidationError("Invalid TCP port.")

        allowed = {"SYN", "ACK", "FIN", "RST", "PSH", "URG"}

        if not set(self.flags).issubset(allowed):
            raise ValidationError("Invalid TCP flag.")

    def header_size(self) -> int:
        return 20


# ============================================================
# 5. INTERNET LAYER
# ============================================================

@dataclass
class IPPacket:
    source: IPv4Address
    destination: IPv4Address
    protocol_number: int
    payload: bytes
    ttl: int = 64
    identification: int = 1

    def __post_init__(self) -> None:
        if not 0 <= self.protocol_number <= 255:
            raise ValidationError("Invalid IP protocol number.")

        if not 1 <= self.ttl <= 255:
            raise ValidationError("TTL must be between 1 and 255.")

        if not 0 <= self.identification <= 65535:
            raise ValidationError("Invalid identification field.")

        if len(self.payload) + 20 > 65535:
            raise ValidationError("IPv4 packet exceeds maximum size.")

    @property
    def total_length(self) -> int:
        return 20 + len(self.payload)

    def checksum(self) -> int:
        header = struct.pack(
            "!BBHHHBBH4s4s",
            0x45,
            0,
            self.total_length,
            self.identification,
            0,
            self.ttl,
            self.protocol_number,
            0,
            socket.inet_aton(self.source.address),
            socket.inet_aton(self.destination.address)
        )

        if len(header) % 2:
            header += b"\x00"

        words = struct.unpack("!10H", header)

        total = sum(words)

        while total >> 16:
            total = (total & 0xFFFF) + (total >> 16)

        return (~total) & 0xFFFF

    def forward(self) -> IPPacket:
        if self.ttl <= 1:
            raise RoutingError("TTL expired; packet discarded.")

        return IPPacket(
            source=self.source,
            destination=self.destination,
            protocol_number=self.protocol_number,
            payload=self.payload,
            ttl=self.ttl - 1,
            identification=self.identification
        )


# ============================================================
# 6. NETWORK ACCESS LAYER
# ============================================================

@dataclass
class EthernetFrame:
    source_mac: str
    destination_mac: str
    payload: bytes
    ether_type: int = 0x0800

    def __post_init__(self) -> None:
        import re

        pattern = r"^(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$"

        for address in (self.source_mac, self.destination_mac):
            if not re.fullmatch(pattern, address):
                raise ValidationError(f"Invalid MAC address: {address}")

        if len(self.payload) > 1500:
            raise ValidationError(
                "Ethernet payload exceeds standard MTU."
            )

    @property
    def frame_size(self) -> int:
        return 14 + len(self.payload) + 4


# ============================================================
# 7. ROUTING TABLE AND PACKET FORWARDING
# ============================================================

@dataclass
class Route:
    network: IPv4Network
    next_hop: str
    interface: str
    metric: int = 1

    def __post_init__(self) -> None:
        if self.metric < 0:
            raise ValidationError("Route metric cannot be negative.")


class Router:
    def __init__(self, name: str) -> None:
        self.name = name
        self.routes: list[Route] = []

    def add_route(self, route: Route) -> None:
        self.routes.append(route)

    def lookup(self, destination: str) -> Route:
        matching = [
            route for route in self.routes
            if route.network.contains(destination)
        ]

        if not matching:
            raise RoutingError(
                f"No route to destination {destination}"
            )

        # Longest-prefix matching selects the most specific route.
        return max(
            matching,
            key=lambda route: (
                route.network.network.prefixlen,
                -route.metric
            )
        )

    def forward_packet(self, packet: IPPacket) -> tuple[IPPacket, Route]:
        route = self.lookup(packet.destination.address)
        forwarded = packet.forward()

        return forwarded, route


# ============================================================
# 8. ENCAPSULATION AND DECAPSULATION
# ============================================================

@dataclass
class EncapsulationResult:
    application_data: ApplicationData
    transport_segment: TCPSegment
    ip_packet: IPPacket
    ethernet_frame: EthernetFrame


class NetworkStack:
    @staticmethod
    def encapsulate(
        application: ApplicationData,
        source_ip: str,
        destination_ip: str,
        source_port: int,
        destination_port: int
    ) -> EncapsulationResult:

        segment = TCPSegment(
            source_port=source_port,
            destination_port=destination_port,
            sequence_number=1000,
            acknowledgment_number=0,
            flags=("ACK", "PSH"),
            payload=application.payload
        )

        packet = IPPacket(
            source=IPv4Address(source_ip),
            destination=IPv4Address(destination_ip),
            protocol_number=6,
            payload=segment.payload
        )

        frame = EthernetFrame(
            source_mac="02:00:00:00:00:01",
            destination_mac="02:00:00:00:00:02",
            payload=packet.payload
        )

        return EncapsulationResult(
            application,
            segment,
            packet,
            frame
        )

    @staticmethod
    def display(result: EncapsulationResult) -> None:
        print("\nENCAPSULATION PROCESS")

        print(
            f"Application: "
            f"{result.application_data.protocol.value}"
        )

        print(
            f"Transport: TCP "
            f"{result.transport_segment.source_port} -> "
            f"{result.transport_segment.destination_port}"
        )

        print(
            f"Internet: "
            f"{result.ip_packet.source.address} -> "
            f"{result.ip_packet.destination.address}"
        )

        print(
            f"Network Access: "
            f"{result.ethernet_frame.source_mac} -> "
            f"{result.ethernet_frame.destination_mac}"
        )

        print(
            f"IP packet length: {result.ip_packet.total_length}"
        )

        print(
            f"IPv4 checksum: "
            f"{result.ip_packet.checksum():04X}"
        )


# ============================================================
# 9. NETWORK MTU AND FRAGMENTATION CALCULATION
# ============================================================

def calculate_ipv4_fragments(
    packet_size: int,
    mtu: int,
    header_size: int = 20
) -> list[int]:
    """
    Calculate fragment payload sizes for IPv4 fragmentation.
    All fragments except the last use multiples of eight bytes.
    """

    if packet_size < header_size:
        raise ValidationError("Packet smaller than IP header.")

    if mtu <= header_size:
        raise ValidationError("MTU must exceed header size.")

    payload_size = packet_size - header_size
    maximum_payload = ((mtu - header_size) // 8) * 8

    fragments = []

    while payload_size > 0:
        fragment_size = min(payload_size, maximum_payload)
        fragments.append(fragment_size)
        payload_size -= fragment_size

    return fragments


# ============================================================
# 10. DNS AND APPLICATION PROTOCOL INTERACTION
# ============================================================

class DNSResolver:
    def __init__(self) -> None:
        self.cache: dict[str, tuple[str, float]] = {}

    def add_record(
        self,
        domain: str,
        address: str,
        ttl: int = 60
    ) -> None:
        if ttl <= 0:
            raise ValidationError("DNS TTL must be positive.")

        ipaddress.IPv4Address(address)

        self.cache[domain.lower()] = (
            address,
            time.monotonic() + ttl
        )

    def resolve(self, domain: str) -> Optional[str]:
        entry = self.cache.get(domain.lower())

        if entry is None:
            return None

        address, expiry = entry

        if time.monotonic() >= expiry:
            del self.cache[domain.lower()]
            return None

        return address


# ============================================================
# 11. NETWORK TROUBLESHOOTING
# ============================================================

@dataclass
class DiagnosticResult:
    component: str
    passed: bool
    message: str


class NetworkDiagnostics:
    @staticmethod
    def check_ip(address: str) -> DiagnosticResult:
        try:
            IPv4Address(address)
            return DiagnosticResult(
                "IP addressing", True, "Valid IPv4 address"
            )
        except ValidationError as exc:
            return DiagnosticResult(
                "IP addressing", False, str(exc)
            )

    @staticmethod
    def check_port(port: int) -> DiagnosticResult:
        passed = 1 <= port <= 65535

        return DiagnosticResult(
            "Transport port",
            passed,
            "Port is valid" if passed else "Invalid port"
        )

    @staticmethod
    def check_ttl(ttl: int) -> DiagnosticResult:
        passed = 1 <= ttl <= 255

        return DiagnosticResult(
            "IP TTL",
            passed,
            "TTL is valid" if passed else "TTL expired or invalid"
        )


# ============================================================
# 12. INTEGRATED NETWORK SCENARIO
# ============================================================

def run_demo() -> None:
    print("=" * 65)
    print("TCP/IP NETWORK STACK SIMULATION")
    print("=" * 65)

    display_architecture()

    print("\nIP ADDRESSING")

    network = IPv4Network.create("192.168.1.0/24")

    print("Network:", network.network)
    print("Broadcast:", network.broadcast_address())
    print("Usable hosts:", network.usable_hosts())
    print(
        "192.168.1.25 belongs to network:",
        network.contains("192.168.1.25")
    )

    print("\nTCP CONNECTION")

    connection = TCPConnection(50000, 443)

    for event in connection.connect():
        print(event)

    print("Connection state:", connection.state.value)

    print("\nAPPLICATION DATA")

    application = ApplicationData.from_text(
        Protocol.HTTPS,
        "GET /api/status HTTP/1.1"
    )

    result = NetworkStack.encapsulate(
        application,
        "192.168.1.10",
        "203.0.113.20",
        50000,
        443
    )

    NetworkStack.display(result)

    print("\nROUTING")

    router = Router("Router-01")

    router.add_route(
        Route(
            IPv4Network.create("203.0.113.0/24"),
            "192.168.1.1",
            "eth0"
        )
    )

    router.add_route(
        Route(
            IPv4Network.create("0.0.0.0/0"),
            "192.168.1.254",
            "eth1",
            metric=10
        )
    )

    forwarded, selected_route = router.forward_packet(
        result.ip_packet
    )

    print("Router:", router.name)
    print("Selected interface:", selected_route.interface)
    print("Next hop:", selected_route.next_hop)
    print("Remaining TTL:", forwarded.ttl)

    print("\nDNS")

    resolver = DNSResolver()
    resolver.add_record("example.com", "93.184.216.34")

    print("example.com:", resolver.resolve("example.com"))

    print("\nFRAGMENTATION")

    fragments = calculate_ipv4_fragments(
        packet_size=4000,
        mtu=1500
    )

    print("Fragment payload sizes:", fragments)

    print("\nNETWORK DIAGNOSTICS")

    tests = [
        NetworkDiagnostics.check_ip("192.168.1.10"),
        NetworkDiagnostics.check_port(443),
        NetworkDiagnostics.check_ttl(64),
        NetworkDiagnostics.check_ip("999.10.10.1")
    ]

    for test in tests:
        print(
            f"{test.component}: "
            f"{'PASS' if test.passed else 'FAIL'} - "
            f"{test.message}"
        )

    print("\nTCP CONNECTION TERMINATION")

    for event in connection.close():
        print(event)

    print("\nSIMULATION COMPLETED")


# ============================================================
# 13. BASIC ASSERTIONS
# ============================================================

def run_tests() -> None:
    assert IPv4Network.create(
        "192.168.1.0/24"
    ).contains("192.168.1.100")

    assert not IPv4Network.create(
        "192.168.1.0/24"
    ).contains("192.168.2.100")

    assert calculate_ipv4_fragments(4000, 1500) == [
        1480, 1480, 1020
    ]

    connection = TCPConnection(40000, 80)
    connection.connect()

    assert connection.state == TCPState.ESTABLISHED

    connection.close()

    assert connection.state == TCPState.CLOSED

    try:
        IPv4Address("300.1.1.1")
        raise AssertionError("Invalid IP was accepted.")
    except ValidationError:
        pass

    print("All assertions passed.")


if __name__ == "__main__":
    run_demo()
    print()
    run_tests()
