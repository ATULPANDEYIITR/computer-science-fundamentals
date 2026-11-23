#!/usr/bin/env python3
"""
Physical and Data Link Layer Simulator
Topics: Signals, binary encoding, frames, MAC addresses, Ethernet,
CRC-32 error detection, switches, MAC learning, and frame forwarding.

Python 3.10+
Standard library only.
"""

from __future__ import annotations

import binascii
import random
import struct
import unittest

from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ============================================================
# 1. FUNDAMENTAL DOMAIN TYPES
# ============================================================

class FrameType(Enum):
    ETHERNET_II = "Ethernet II"
    BROADCAST = "Broadcast"


class PortState(Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class TransmissionError(Exception):
    """Raised when a frame cannot be transmitted or decoded."""


# ============================================================
# 2. MAC ADDRESS MANAGEMENT
# ============================================================

@dataclass(frozen=True)
class MACAddress:
    value: str

    def __post_init__(self):
        normalized = self.value.upper().replace("-", ":")
        parts = normalized.split(":")

        if len(parts) != 6:
            raise ValueError("A MAC address must contain six octets.")

        try:
            octets = [int(part, 16) for part in parts]
        except ValueError as exc:
            raise ValueError("Invalid hexadecimal MAC address.") from exc

        if any(not 0 <= octet <= 255 for octet in octets):
            raise ValueError("MAC octets must be between 00 and FF.")

        object.__setattr__(
            self,
            "value",
            ":".join(f"{octet:02X}" for octet in octets)
        )

    @property
    def octets(self) -> bytes:
        return bytes(int(part, 16) for part in self.value.split(":"))

    @property
    def is_broadcast(self) -> bool:
        return self.octets == b"\xff" * 6

    @property
    def is_multicast(self) -> bool:
        return bool(self.octets[0] & 1)

    @property
    def is_unicast(self) -> bool:
        return not self.is_multicast

    def __str__(self) -> str:
        return self.value


BROADCAST_MAC = MACAddress("FF:FF:FF:FF:FF:FF")


# ============================================================
# 3. PHYSICAL LAYER: SIGNAL ENCODING
# ============================================================

class LineEncoder:
    """
    Represents digital bit streams using physical signal levels.

    NRZ:
        0 -> low
        1 -> high

    Manchester:
        0 -> low, high
        1 -> high, low

    Manchester decoding checks mandatory mid-bit transitions.
    """

    @staticmethod
    def validate_bits(bits: str) -> None:
        if not bits:
            raise ValueError("Bit sequence cannot be empty.")

        if any(bit not in "01" for bit in bits):
            raise ValueError("Bit sequence must contain only 0 and 1.")

    @classmethod
    def encode_nrz(cls, bits: str) -> list[int]:
        cls.validate_bits(bits)
        return [int(bit) for bit in bits]

    @classmethod
    def decode_nrz(cls, signals: list[int]) -> str:
        if not signals or any(signal not in (0, 1) for signal in signals):
            raise ValueError("Invalid NRZ signal levels.")

        return "".join(str(signal) for signal in signals)

    @classmethod
    def encode_manchester(cls, bits: str) -> list[int]:
        cls.validate_bits(bits)

        signals = []

        for bit in bits:
            signals.extend([0, 1] if bit == "0" else [1, 0])

        return signals

    @staticmethod
    def decode_manchester(signals: list[int]) -> str:
        if not signals or len(signals) % 2:
            raise ValueError("Manchester signal requires complete bit pairs.")

        if any(signal not in (0, 1) for signal in signals):
            raise ValueError("Invalid signal level.")

        bits = []

        for index in range(0, len(signals), 2):
            pair = signals[index:index + 2]

            if pair == [0, 1]:
                bits.append("0")
            elif pair == [1, 0]:
                bits.append("1")
            else:
                raise TransmissionError(
                    f"Invalid Manchester transition at bit {index // 2}."
                )

        return "".join(bits)


# ============================================================
# 4. PHYSICAL SIGNAL CHARACTERISTICS
# ============================================================

@dataclass
class Signal:
    bits: str
    bit_rate: int
    amplitude: float
    noise_probability: float = 0.0

    def __post_init__(self):
        LineEncoder.validate_bits(self.bits)

        if self.bit_rate <= 0:
            raise ValueError("Bit rate must be positive.")

        if self.amplitude <= 0:
            raise ValueError("Amplitude must be positive.")

        if not 0 <= self.noise_probability <= 1:
            raise ValueError("Noise probability must be between 0 and 1.")

    @property
    def duration_seconds(self) -> float:
        return len(self.bits) / self.bit_rate

    @property
    def bandwidth_bits_per_second(self) -> int:
        return self.bit_rate

    def transmit(self, seed: Optional[int] = None) -> str:
        """Simulate a noisy digital transmission."""
        generator = random.Random(seed)
        received = []

        for bit in self.bits:
            if generator.random() < self.noise_probability:
                received.append("1" if bit == "0" else "0")
            else:
                received.append(bit)

        return "".join(received)


# ============================================================
# 5. DATA LINK LAYER: ETHERNET FRAME
# ============================================================

@dataclass
class EthernetFrame:
    destination: MACAddress
    source: MACAddress
    payload: bytes
    ether_type: int = 0x0800

    MIN_PAYLOAD = 46
    MAX_PAYLOAD = 1500
    HEADER_LENGTH = 14
    FCS_LENGTH = 4

    def __post_init__(self):
        if self.source.is_multicast:
            raise ValueError("Ethernet source must be an individual MAC.")

        if self.destination == self.source:
            raise ValueError("Source and destination must differ.")

        if not 0 <= self.ether_type <= 65535:
            raise ValueError("EtherType must fit into 16 bits.")

        if len(self.payload) > self.MAX_PAYLOAD:
            raise ValueError("Payload exceeds Ethernet MTU.")

    @property
    def padded_payload(self) -> bytes:
        return self.payload.ljust(self.MIN_PAYLOAD, b"\x00")

    def header(self) -> bytes:
        return (
            self.destination.octets
            + self.source.octets
            + struct.pack("!H", self.ether_type)
        )

    def without_fcs(self) -> bytes:
        return self.header() + self.padded_payload

    def calculate_fcs(self) -> int:
        return binascii.crc32(self.without_fcs()) & 0xFFFFFFFF

    def serialize(self) -> bytes:
        return self.without_fcs() + struct.pack("!I", self.calculate_fcs())

    @classmethod
    def deserialize(cls, raw: bytes) -> EthernetFrame:
        if len(raw) < cls.HEADER_LENGTH + cls.MIN_PAYLOAD + cls.FCS_LENGTH:
            raise TransmissionError("Ethernet frame is too short.")

        if len(raw) > cls.HEADER_LENGTH + cls.MAX_PAYLOAD + cls.FCS_LENGTH:
            raise TransmissionError("Ethernet frame exceeds maximum size.")

        content = raw[:-4]
        received_fcs = struct.unpack("!I", raw[-4:])[0]
        calculated_fcs = binascii.crc32(content) & 0xFFFFFFFF

        if received_fcs != calculated_fcs:
            raise TransmissionError("CRC/FCS verification failed.")

        destination = MACAddress(":".join(
            f"{value:02X}" for value in raw[0:6]
        ))

        source = MACAddress(":".join(
            f"{value:02X}" for value in raw[6:12]
        ))

        ether_type = struct.unpack("!H", raw[12:14])[0]

        return cls(
            destination=destination,
            source=source,
            payload=raw[14:-4],
            ether_type=ether_type
        )


# ============================================================
# 6. NETWORK INTERFACES
# ============================================================

@dataclass
class NetworkInterface:
    name: str
    mac: MACAddress
    state: PortState = PortState.ACTIVE
    received_frames: int = 0
    transmitted_frames: int = 0
    dropped_frames: int = 0

    def receive(self, frame: EthernetFrame) -> None:
        if self.state != PortState.ACTIVE:
            self.dropped_frames += 1
            raise TransmissionError(f"{self.name} is disabled.")

        self.received_frames += 1

    def transmit(self, frame: EthernetFrame) -> None:
        if self.state != PortState.ACTIVE:
            self.dropped_frames += 1
            raise TransmissionError(f"{self.name} is disabled.")

        self.transmitted_frames += 1


# ============================================================
# 7. ETHERNET SWITCH: MAC LEARNING AND FORWARDING
# ============================================================

@dataclass
class MACEntry:
    port: str
    last_seen: int


@dataclass
class EthernetSwitch:
    name: str
    aging_time: int = 300
    interfaces: dict[str, NetworkInterface] = field(default_factory=dict)
    mac_table: OrderedDict = field(default_factory=OrderedDict)
    clock: int = 0

    def __post_init__(self):
        if self.aging_time <= 0:
            raise ValueError("Aging time must be positive.")

    def add_interface(self, interface: NetworkInterface) -> None:
        if interface.name in self.interfaces:
            raise ValueError("Duplicate switch interface.")

        self.interfaces[interface.name] = interface

    def _expire_entries(self) -> None:
        expired = [
            mac for mac, entry in self.mac_table.items()
            if self.clock - entry.last_seen >= self.aging_time
        ]

        for mac in expired:
            del self.mac_table[mac]

    def learn(self, source: MACAddress, incoming_port: str) -> None:
        if source.is_multicast:
            raise TransmissionError("Cannot learn a multicast source MAC.")

        self.mac_table[source] = MACEntry(
            port=incoming_port,
            last_seen=self.clock
        )

    def forward(
        self,
        frame: EthernetFrame,
        incoming_port: str
    ) -> list[str]:

        if incoming_port not in self.interfaces:
            raise TransmissionError("Unknown incoming port.")

        incoming = self.interfaces[incoming_port]

        incoming.receive(frame)

        self.clock += 1
        self._expire_entries()

        # Learn the source address before making a forwarding decision.
        self.learn(frame.source, incoming_port)

        if frame.destination == frame.source:
            return []

        # Broadcast and multicast frames are flooded.
        if frame.destination.is_multicast:
            destinations = [
                port for port, interface in self.interfaces.items()
                if port != incoming_port
                and interface.state == PortState.ACTIVE
            ]
        else:
            entry = self.mac_table.get(frame.destination)

            if entry is None:
                destinations = [
                    port for port, interface in self.interfaces.items()
                    if port != incoming_port
                    and interface.state == PortState.ACTIVE
                ]

            elif entry.port == incoming_port:
                # Destination is already reachable through this port.
                destinations = []

            else:
                destinations = [entry.port]

        forwarded = []

        for port in destinations:
            interface = self.interfaces[port]

            try:
                interface.transmit(frame)
                forwarded.append(port)
            except TransmissionError:
                continue

        return forwarded

    def display_mac_table(self) -> None:
        print(f"\nMAC Address Table: {self.name}")
        print("-" * 48)

        if not self.mac_table:
            print("No learned addresses.")
            return

        for mac, entry in self.mac_table.items():
            print(
                f"{str(mac):20} "
                f"{entry.port:10} "
                f"Last seen: {entry.last_seen}"
            )


# ============================================================
# 8. NETWORK SIMULATION
# ============================================================

def demonstrate_physical_layer() -> None:
    print("\nPHYSICAL LAYER")
    print("=" * 60)

    bits = "10110010"

    nrz = LineEncoder.encode_nrz(bits)
    manchester = LineEncoder.encode_manchester(bits)

    print("Original bits:       ", bits)
    print("NRZ signals:         ", nrz)
    print("Manchester signals:  ", manchester)

    print("NRZ decoded:         ", LineEncoder.decode_nrz(nrz))
    print(
        "Manchester decoded:  ",
        LineEncoder.decode_manchester(manchester)
    )

    signal = Signal(
        bits=bits,
        bit_rate=1_000_000,
        amplitude=5.0
    )

    print(f"Bit rate: {signal.bit_rate} bits/second")
    print(f"Transmission time: {signal.duration_seconds:.8f} seconds")


def demonstrate_ethernet() -> None:
    print("\nDATA LINK LAYER: ETHERNET")
    print("=" * 60)

    host_a = MACAddress("00:11:22:33:44:AA")
    host_b = MACAddress("00:11:22:33:44:BB")
    host_c = MACAddress("00:11:22:33:44:CC")

    switch = EthernetSwitch("SW-CORE", aging_time=10)

    switch.add_interface(NetworkInterface("eth0", host_a))
    switch.add_interface(NetworkInterface("eth1", host_b))
    switch.add_interface(NetworkInterface("eth2", host_c))

    frame_ab = EthernetFrame(
        destination=host_b,
        source=host_a,
        payload=b"Hello from Host A"
    )

    serialized = frame_ab.serialize()

    print(f"Serialized Ethernet frame: {len(serialized)} bytes")
    print(f"EtherType: 0x{frame_ab.ether_type:04X}")
    print(f"FCS: 0x{frame_ab.calculate_fcs():08X}")

    decoded = EthernetFrame.deserialize(serialized)

    print("Frame integrity: VALID")
    print(f"Source MAC: {decoded.source}")
    print(f"Destination MAC: {decoded.destination}")

    # Initially, the switch does not know Host B.
    result = switch.forward(frame_ab, "eth0")
    print("\nFirst transmission (unknown destination):")
    print("Forwarded ports:", result)

    # Host B responds. Its MAC address is learned.
    response = EthernetFrame(
        destination=host_a,
        source=host_b,
        payload=b"Response from Host B"
    )

    result = switch.forward(response, "eth1")
    print("\nSecond transmission (known destination):")
    print("Forwarded ports:", result)

    # Host A now sends to a known destination.
    result = switch.forward(frame_ab, "eth0")
    print("\nThird transmission (learned destination):")
    print("Forwarded ports:", result)

    # Broadcast demonstration.
    broadcast = EthernetFrame(
        destination=BROADCAST_MAC,
        source=host_a,
        payload=b"Network discovery"
    )

    print("\nBroadcast transmission:")
    print("Forwarded ports:", switch.forward(broadcast, "eth0"))

    switch.display_mac_table()

    # Demonstrate error detection.
    corrupted = bytearray(serialized)
    corrupted[15] ^= 0x01

    print("\nCorruption test:")

    try:
        EthernetFrame.deserialize(bytes(corrupted))
    except TransmissionError as error:
        print("Frame rejected:", error)


# ============================================================
# 9. VALIDATION AND AUTOMATED TESTS
# ============================================================

class NetworkTests(unittest.TestCase):

    def test_mac_normalization(self):
        self.assertEqual(
            str(MACAddress("00-11-22-33-44-aa")),
            "00:11:22:33:44:AA"
        )

    def test_manchester_round_trip(self):
        bits = "11001010"

        self.assertEqual(
            LineEncoder.decode_manchester(
                LineEncoder.encode_manchester(bits)
            ),
            bits
        )

    def test_invalid_manchester_signal(self):
        with self.assertRaises(TransmissionError):
            LineEncoder.decode_manchester([0, 0])

    def test_ethernet_crc(self):
        frame = EthernetFrame(
            MACAddress("00:11:22:33:44:BB"),
            MACAddress("00:11:22:33:44:AA"),
            b"Test"
        )

        self.assertEqual(
            EthernetFrame.deserialize(frame.serialize()).payload,
            frame.padded_payload
        )

    def test_corrupted_frame(self):
        frame = EthernetFrame(
            MACAddress("00:11:22:33:44:BB"),
            MACAddress("00:11:22:33:44:AA"),
            b"Test"
        )

        raw = bytearray(frame.serialize())
        raw[14] ^= 1

        with self.assertRaises(TransmissionError):
            EthernetFrame.deserialize(bytes(raw))

    def test_switch_learning(self):
        a = MACAddress("00:00:00:00:00:01")
        b = MACAddress("00:00:00:00:00:02")

        switch = EthernetSwitch("TEST")

        switch.add_interface(NetworkInterface("p1", a))
        switch.add_interface(NetworkInterface("p2", b))

        frame = EthernetFrame(b, a, b"data")

        self.assertEqual(switch.forward(frame, "p1"), ["p2"])

        response = EthernetFrame(a, b, b"reply")

        self.assertEqual(switch.forward(response, "p2"), ["p1"])

    def test_unknown_destination_flooding(self):
        a = MACAddress("00:00:00:00:00:01")
        b = MACAddress("00:00:00:00:00:02")
        c = MACAddress("00:00:00:00:00:03")

        switch = EthernetSwitch("TEST")

        for port, mac in [("p1", a), ("p2", b), ("p3", c)]:
            switch.add_interface(NetworkInterface(port, mac))

        frame = EthernetFrame(b, a, b"data")

        self.assertEqual(
            switch.forward(frame, "p1"),
            ["p2", "p3"]
        )


def main() -> None:
    demonstrate_physical_layer()
    demonstrate_ethernet()

    print("\nAUTOMATED TESTS")
    print("=" * 60)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NetworkTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
