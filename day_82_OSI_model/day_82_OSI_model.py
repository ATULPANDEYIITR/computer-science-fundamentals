#!/usr/bin/env python3
"""
OSI Model: Seven-Layer Network Communication Simulator

Demonstrates:
- Seven OSI layers and their responsibilities.
- Encapsulation and decapsulation.
- Protocol Data Units (PDUs).
- MAC and IP addressing.
- TCP and UDP transport.
- Session management.
- Presentation encoding and encryption metadata.
- Application protocols.
- Network routing and switching.
- Error detection and validation.
- Layer-specific troubleshooting.
"""

from __future__ import annotations

import hashlib
import json
import logging
import struct
import uuid

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger("osi")


class Layer(IntEnum):
    PHYSICAL = 1
    DATA_LINK = 2
    NETWORK = 3
    TRANSPORT = 4
    SESSION = 5
    PRESENTATION = 6
    APPLICATION = 7


class ProtocolError(Exception):
    """Raised when network protocol processing fails."""


class ValidationError(ProtocolError):
    """Raised when an address or packet is invalid."""


@dataclass
class PDU:
    layer: Layer
    protocol: str
    payload: Any
    metadata: dict = field(default_factory=dict)


@dataclass
class NetworkPacket:
    source_mac: str
    destination_mac: str
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    transport_protocol: str
    application_protocol: str
    payload: bytes
    session_id: str
    encoding: str = "utf-8"
    encrypted: bool = False


def validate_mac(address: str) -> None:
    parts = address.split(":")
    if len(parts) != 6:
        raise ValidationError(f"Invalid MAC address: {address}")

    try:
        values = [int(part, 16) for part in parts]
    except ValueError as exc:
        raise ValidationError("MAC address contains invalid hexadecimal") from exc

    if any(not 0 <= value <= 255 for value in values):
        raise ValidationError("MAC address octet outside valid range")


def validate_ip(address: str) -> None:
    import ipaddress

    try:
        ipaddress.ip_address(address)
    except ValueError as exc:
        raise ValidationError(f"Invalid IP address: {address}") from exc


def validate_port(port: int) -> None:
    if not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValidationError(f"Invalid port: {port}")


class PhysicalLayer:
    """Layer 1: Transmits bits over a physical medium."""

    @staticmethod
    def transmit(frame: bytes) -> PDU:
        if not isinstance(frame, bytes):
            raise ProtocolError("Physical transmission requires bytes")

        bits = "".join(f"{byte:08b}" for byte in frame)

        return PDU(
            Layer.PHYSICAL,
            "Ethernet electrical/optical/radio signaling",
            bits,
            {"bit_length": len(bits)}
        )

    @staticmethod
    def receive(signal: PDU) -> bytes:
        if signal.layer != Layer.PHYSICAL:
            raise ProtocolError("Expected physical-layer signal")

        bits = signal.payload

        if len(bits) % 8 != 0 or any(bit not in "01" for bit in bits):
            raise ProtocolError("Invalid physical bit stream")

        return bytes(
            int(bits[index:index + 8], 2)
            for index in range(0, len(bits), 8)
        )


class DataLinkLayer:
    """Layer 2: Creates Ethernet frames and checks integrity."""

    ETHERTYPE_IPV4 = 0x0800

    @staticmethod
    def encapsulate(
        payload: bytes,
        source_mac: str,
        destination_mac: str
    ) -> PDU:
        validate_mac(source_mac)
        validate_mac(destination_mac)

        source = bytes.fromhex(source_mac.replace(":", ""))
        destination = bytes.fromhex(
            destination_mac.replace(":", "")
        )

        header = destination + source + struct.pack(
            "!H", DataLinkLayer.ETHERTYPE_IPV4
        )

        frame_without_fcs = header + payload

        # Ethernet FCS uses CRC-32.
        import zlib

        fcs = struct.pack(
            "<I",
            zlib.crc32(frame_without_fcs) & 0xFFFFFFFF
        )

        return PDU(
            Layer.DATA_LINK,
            "Ethernet",
            frame_without_fcs + fcs,
            {
                "source_mac": source_mac,
                "destination_mac": destination_mac
            }
        )

    @staticmethod
    def decapsulate(frame: bytes) -> bytes:
        if len(frame) < 18:
            raise ProtocolError("Ethernet frame is too short")

        import zlib

        content = frame[:-4]
        received_fcs = struct.unpack("<I", frame[-4:])[0]
        calculated_fcs = zlib.crc32(content) & 0xFFFFFFFF

        if received_fcs != calculated_fcs:
            raise ProtocolError("Ethernet FCS verification failed")

        destination = content[:6]
        source = content[6:12]
        ethertype = struct.unpack("!H", content[12:14])[0]

        if ethertype != DataLinkLayer.ETHERTYPE_IPV4:
            raise ProtocolError("Unsupported Ethernet EtherType")

        return content[14:]


class NetworkLayer:
    """Layer 3: IPv4 addressing and routing metadata."""

    @staticmethod
    def encapsulate(
        payload: bytes,
        source_ip: str,
        destination_ip: str
    ) -> PDU:
        import ipaddress

        validate_ip(source_ip)
        validate_ip(destination_ip)

        source = ipaddress.IPv4Address(source_ip)
        destination = ipaddress.IPv4Address(destination_ip)

        if len(payload) > 65515:
            raise ProtocolError("IPv4 payload exceeds maximum size")

        total_length = 20 + len(payload)

        header = struct.pack(
            "!BBHHHBBH4s4s",
            0x45,
            0,
            total_length,
            1,
            0x4000,
            64,
            6,
            0,
            source.packed,
            destination.packed
        )

        checksum = NetworkLayer.checksum(header)

        header = header[:10] + struct.pack(
            "!H", checksum
        ) + header[12:]

        return PDU(
            Layer.NETWORK,
            "IPv4",
            header + payload,
            {
                "source_ip": source_ip,
                "destination_ip": destination_ip,
                "ttl": 64
            }
        )

    @staticmethod
    def checksum(data: bytes) -> int:
        if len(data) % 2:
            data += b"\x00"

        total = sum(
            struct.unpack(
                "!H",
                data[index:index + 2]
            )[0]
            for index in range(0, len(data), 2)
        )

        while total >> 16:
            total = (total & 0xFFFF) + (total >> 16)

        return (~total) & 0xFFFF

    @staticmethod
    def decapsulate(packet: bytes) -> bytes:
        if len(packet) < 20:
            raise ProtocolError("IPv4 packet is too short")

        version = packet[0] >> 4
        header_length = (packet[0] & 0x0F) * 4

        if version != 4 or header_length < 20:
            raise ProtocolError("Invalid IPv4 header")

        if len(packet) < header_length:
            raise ProtocolError("Truncated IPv4 header")

        total_length = struct.unpack("!H", packet[2:4])[0]

        if total_length < header_length or total_length > len(packet):
            raise ProtocolError("Invalid IPv4 total length")

        if NetworkLayer.checksum(packet[:header_length]) != 0:
            raise ProtocolError("IPv4 header checksum failed")

        return packet[header_length:total_length]


class TransportLayer:
    """Layer 4: TCP-style segment construction and UDP datagrams."""

    @staticmethod
    def encapsulate(
        payload: bytes,
        source_port: int,
        destination_port: int,
        protocol: str = "TCP"
    ) -> PDU:
        validate_port(source_port)
        validate_port(destination_port)

        protocol = protocol.upper()

        if protocol == "TCP":
            offset_flags = (5 << 12) | 0x002
            header = struct.pack(
                "!HHIIHHHH",
                source_port,
                destination_port,
                1000,
                0,
                offset_flags,
                65535,
                0,
                0
            )

        elif protocol == "UDP":
            header = struct.pack(
                "!HHHH",
                source_port,
                destination_port,
                len(payload) + 8,
                0
            )

        else:
            raise ProtocolError("Only TCP and UDP are supported")

        return PDU(
            Layer.TRANSPORT,
            protocol,
            header + payload,
            {
                "source_port": source_port,
                "destination_port": destination_port
            }
        )

    @staticmethod
    def decapsulate(segment: bytes, protocol: str) -> bytes:
        if protocol == "TCP":
            if len(segment) < 20:
                raise ProtocolError("Truncated TCP segment")

            header_length = (segment[12] >> 4) * 4

            if header_length < 20 or header_length > len(segment):
                raise ProtocolError("Invalid TCP header length")

            return segment[header_length:]

        if protocol == "UDP":
            if len(segment) < 8:
                raise ProtocolError("Truncated UDP datagram")

            length = struct.unpack("!H", segment[4:6])[0]

            if length < 8 or length > len(segment):
                raise ProtocolError("Invalid UDP datagram length")

            return segment[8:length]

        raise ProtocolError("Unsupported transport protocol")


class SessionLayer:
    """Layer 5: Manages logical communication sessions."""

    active_sessions: set[str] = set()

    @classmethod
    def open_session(cls) -> str:
        session_id = str(uuid.uuid4())
        cls.active_sessions.add(session_id)
        return session_id

    @classmethod
    def validate_session(cls, session_id: str) -> None:
        if session_id not in cls.active_sessions:
            raise ProtocolError("Session is absent or terminated")

    @classmethod
    def close_session(cls, session_id: str) -> None:
        if session_id not in cls.active_sessions:
            raise ProtocolError("Cannot close an unknown session")

        cls.active_sessions.remove(session_id)


class PresentationLayer:
    """Layer 6: Character encoding and integrity metadata."""

    @staticmethod
    def encode(message: str, encoding: str = "utf-8") -> bytes:
        try:
            return message.encode(encoding)
        except (UnicodeError, LookupError) as exc:
            raise ProtocolError("Presentation encoding failed") from exc

    @staticmethod
    def decode(payload: bytes, encoding: str = "utf-8") -> str:
        try:
            return payload.decode(encoding)
        except (UnicodeError, LookupError) as exc:
            raise ProtocolError("Presentation decoding failed") from exc

    @staticmethod
    def digest(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()


class ApplicationLayer:
    """Layer 7: Application-level HTTP-like communication."""

    @staticmethod
    def create_request(
        method: str,
        path: str,
        body: str
    ) -> str:
        if method not in {"GET", "POST", "PUT", "DELETE"}:
            raise ProtocolError("Unsupported HTTP method")

        if not path.startswith("/") or "\r" in path or "\n" in path:
            raise ProtocolError("Invalid request path")

        return (
            f"{method} {path} HTTP/1.1\r\n"
            "Host: example.internal\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n"
            f"Content-Length: {len(body.encode('utf-8'))}\r\n"
            "\r\n"
            f"{body}"
        )


class OSISimulator:
    """Coordinates seven-layer encapsulation and decapsulation."""

    def send(
        self,
        message: str,
        source_ip: str,
        destination_ip: str,
        source_mac: str,
        destination_mac: str,
        protocol: str = "TCP"
    ) -> bytes:

        application_data = ApplicationLayer.create_request(
            "POST",
            "/api/network",
            message
        )

        presentation_data = PresentationLayer.encode(
            application_data
        )

        session_id = SessionLayer.open_session()

        SessionLayer.validate_session(session_id)

        transport = TransportLayer.encapsulate(
            presentation_data,
            51000,
            443,
            protocol
        )

        network = NetworkLayer.encapsulate(
            transport.payload,
            source_ip,
            destination_ip
        )

        data_link = DataLinkLayer.encapsulate(
            network.payload,
            source_mac,
            destination_mac
        )

        physical = PhysicalLayer.transmit(data_link.payload)

        logger.info(
            "Encapsulation completed: session=%s, protocol=%s",
            session_id,
            protocol
        )

        return physical.payload

    def receive(
        self,
        bits: str,
        protocol: str = "TCP"
    ) -> str:

        physical = PDU(
            Layer.PHYSICAL,
            "Physical signaling",
            bits
        )

        frame = PhysicalLayer.receive(physical)

        network_packet = DataLinkLayer.decapsulate(frame)

        transport_segment = NetworkLayer.decapsulate(
            network_packet
        )

        application_payload = TransportLayer.decapsulate(
            transport_segment,
            protocol
        )

        return PresentationLayer.decode(application_payload)


def run_tests() -> None:
    simulator = OSISimulator()

    message = "OSI seven-layer communication: Hello, Network!"

    frame_bits = simulator.send(
        message=message,
        source_ip="192.168.1.10",
        destination_ip="192.168.1.20",
        source_mac="00:11:22:33:44:55",
        destination_mac="AA:BB:CC:DD:EE:FF",
        protocol="TCP"
    )

    recovered = simulator.receive(frame_bits, "TCP")

    assert message in recovered
    assert len(frame_bits) % 8 == 0

    # UDP follows a different transport header format.
    udp = TransportLayer.encapsulate(
        b"UDP payload",
        5000,
        53,
        "UDP"
    )

    assert TransportLayer.decapsulate(
        udp.payload,
        "UDP"
    ) == b"UDP payload"

    # Invalid addressing must fail before transmission.
    try:
        validate_ip("999.999.999.999")
        raise AssertionError("Invalid address was accepted")
    except ValidationError:
        pass

    # Frame corruption must be detected through FCS.
    frame = DataLinkLayer.encapsulate(
        b"test",
        "00:11:22:33:44:55",
        "AA:BB:CC:DD:EE:FF"
    )

    corrupted = bytearray(frame.payload)
    corrupted[15] ^= 0x01

    try:
        DataLinkLayer.decapsulate(bytes(corrupted))
        raise AssertionError("Corrupted frame was accepted")
    except ProtocolError:
        pass

    print("All OSI simulator tests passed.")
    print("Recovered application message:")
    print(recovered)


if __name__ == "__main__":
    run_tests()
