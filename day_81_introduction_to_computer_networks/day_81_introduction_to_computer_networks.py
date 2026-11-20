#!/usr/bin/env python3
"""
INTRODUCTION TO COMPUTER NETWORKS
Topics: Networks, LAN, WAN, Network Models, Packet Switching.

A self-contained network simulation covering:
- Network devices and interfaces
- LAN and WAN topology
- OSI and TCP/IP models
- IP addressing and subnet validation
- Packet creation and encapsulation
- Packet switching and routing
- Forwarding tables and next-hop selection
- TTL and packet loss
- Network performance measurements
- Basic connectivity testing
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from ipaddress import IPv4Address, IPv4Network, ip_network
from collections import defaultdict, deque
from typing import Optional
import json
import time


# ============================================================
# 1. NETWORK MODELS
# ============================================================

class OSILayer(Enum):
    PHYSICAL = 1
    DATA_LINK = 2
    NETWORK = 3
    TRANSPORT = 4
    SESSION = 5
    PRESENTATION = 6
    APPLICATION = 7


OSI_DESCRIPTIONS = {
    1: "Transmission of raw bits through physical media",
    2: "Frames, MAC addresses and local delivery",
    3: "Logical addressing and routing",
    4: "End-to-end transport using TCP or UDP",
    5: "Session establishment and management",
    6: "Data representation, encoding and encryption",
    7: "Network applications and user services",
}

TCP_IP_MODEL = {
    "Application": [5, 6, 7],
    "Transport": [4],
    "Internet": [3],
    "Network Access": [1, 2],
}


def display_network_models() -> None:
    print("\nOSI MODEL")
    for layer in reversed(list(OSILayer)):
        print(f"Layer {layer.value}: {layer.name:15} "
              f"- {OSI_DESCRIPTIONS[layer.value]}")

    print("\nTCP/IP MODEL")
    for name, layers in TCP_IP_MODEL.items():
        print(f"{name:16} -> OSI layers {layers}")


# ============================================================
# 2. NETWORK DEVICE DOMAIN
# ============================================================

class DeviceType(Enum):
    HOST = "host"
    SWITCH = "switch"
    ROUTER = "router"


class NetworkType(Enum):
    LAN = "LAN"
    WAN = "WAN"


@dataclass
class NetworkInterface:
    name: str
    ip_address: IPv4Address
    subnet: IPv4Network
    mac_address: str

    def __post_init__(self):
        if self.ip_address not in self.subnet:
            raise ValueError("Interface IP is outside its subnet")

        parts = self.mac_address.split(":")
        if len(parts) != 6:
            raise ValueError("Invalid MAC address")

        try:
            if any(len(part) != 2 or
                   int(part, 16) > 255 for part in parts):
                raise ValueError
        except ValueError:
            raise ValueError("Invalid MAC address format") from None

        self.mac_address = self.mac_address.upper()

    @property
    def network_address(self) -> str:
        return str(self.subnet.network_address)


@dataclass
class NetworkDevice:
    device_id: str
    name: str
    device_type: DeviceType
    interfaces: list[NetworkInterface] = field(default_factory=list)

    def add_interface(self, interface: NetworkInterface) -> None:
        if any(i.name == interface.name for i in self.interfaces):
            raise ValueError("Interface name already exists")

        self.interfaces.append(interface)

    def get_interface(self, ip: IPv4Address) -> Optional[NetworkInterface]:
        return next(
            (interface for interface in self.interfaces
             if interface.ip_address == ip),
            None
        )


# ============================================================
# 3. PACKET MODEL
# ============================================================

class Protocol(Enum):
    ICMP = "ICMP"
    TCP = "TCP"
    UDP = "UDP"


@dataclass
class Packet:
    packet_id: int
    source_ip: IPv4Address
    destination_ip: IPv4Address
    protocol: Protocol
    payload: bytes
    ttl: int = 64
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    hops: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.ttl < 1 or self.ttl > 255:
            raise ValueError("TTL must be between 1 and 255")

        if len(self.payload) > 65507:
            raise ValueError("Payload exceeds simulation limit")

        for port in (self.source_port, self.destination_port):
            if port is not None and not 1 <= port <= 65535:
                raise ValueError("Port must be between 1 and 65535")

    @property
    def size_bytes(self) -> int:
        # IPv4 header plus simulated transport header.
        transport_header = 20 if self.protocol == Protocol.TCP else 8
        return 20 + transport_header + len(self.payload)

    def decrement_ttl(self) -> bool:
        self.ttl -= 1
        return self.ttl > 0


# ============================================================
# 4. NETWORK TOPOLOGY
# ============================================================

@dataclass
class Link:
    source: str
    destination: str
    network_type: NetworkType
    bandwidth_mbps: float
    latency_ms: float
    available: bool = True

    def __post_init__(self):
        if self.bandwidth_mbps <= 0 or self.latency_ms < 0:
            raise ValueError("Invalid link performance parameters")


class NetworkTopology:
    def __init__(self):
        self.devices: dict[str, NetworkDevice] = {}
        self.adjacency: dict[str, list[Link]] = defaultdict(list)

    def add_device(self, device: NetworkDevice) -> None:
        if device.device_id in self.devices:
            raise ValueError("Duplicate device ID")

        self.devices[device.device_id] = device

    def connect(self, link: Link) -> None:
        if link.source not in self.devices:
            raise ValueError("Source device does not exist")

        if link.destination not in self.devices:
            raise ValueError("Destination device does not exist")

        if link.source == link.destination:
            raise ValueError("Self-connections are not allowed")

        if any(existing.destination == link.destination
               for existing in self.adjacency[link.source]):
            raise ValueError("Duplicate directed connection")

        self.adjacency[link.source].append(link)

    def shortest_path(self, source: str, destination: str) -> list[str]:
        if source not in self.devices or destination not in self.devices:
            raise ValueError("Unknown source or destination")

        queue = deque([[source]])
        visited = {source}

        while queue:
            path = queue.popleft()
            current = path[-1]

            if current == destination:
                return path

            for link in self.adjacency[current]:
                if link.available and link.destination not in visited:
                    visited.add(link.destination)
                    queue.append(path + [link.destination])

        raise ConnectionError("No available route")

    def set_link_status(self, source: str, destination: str,
                        available: bool) -> None:
        for link in self.adjacency.get(source, []):
            if link.destination == destination:
                link.available = available
                return

        raise ValueError("Link not found")


# ============================================================
# 5. IP ADDRESSING AND SUBNETTING
# ============================================================

def analyze_subnet(cidr: str) -> dict:
    network = ip_network(cidr, strict=False)

    if network.version != 4:
        raise ValueError("This simulation supports IPv4 only")

    hosts = list(network.hosts()) if network.num_addresses > 2 else []

    return {
        "network": str(network.network_address),
        "broadcast": str(network.broadcast_address),
        "subnet_mask": str(network.netmask),
        "prefix": network.prefixlen,
        "total_addresses": network.num_addresses,
        "usable_hosts": max(0, network.num_addresses - 2),
        "first_host": str(hosts[0]) if hosts else None,
        "last_host": str(hosts[-1]) if hosts else None,
    }


# ============================================================
# 6. ROUTING TABLE
# ============================================================

@dataclass
class Route:
    network: IPv4Network
    next_hop: str
    metric: int = 1


class RoutingTable:
    def __init__(self):
        self.routes: list[Route] = []

    def add_route(self, route: Route) -> None:
        if route.metric < 0:
            raise ValueError("Route metric cannot be negative")

        self.routes.append(route)

    def lookup(self, destination: IPv4Address) -> Optional[Route]:
        # Longest-prefix matching selects the most specific route.
        matching = [
            route for route in self.routes
            if destination in route.network
        ]

        if not matching:
            return None

        return max(
            matching,
            key=lambda route: (route.network.prefixlen, -route.metric)
        )


# ============================================================
# 7. PACKET SWITCHING ENGINE
# ============================================================

class PacketSwitch:
    def __init__(self, topology: NetworkTopology):
        self.topology = topology
        self.routing_table = RoutingTable()
        self.next_packet_id = 1
        self.delivered = 0
        self.dropped = 0
        self.transmitted_bytes = 0

    def create_packet(
        self,
        source: str,
        destination: str,
        payload: str,
        protocol: Protocol = Protocol.TCP,
        ttl: int = 64,
        source_port: Optional[int] = None,
        destination_port: Optional[int] = None,
    ) -> Packet:

        packet = Packet(
            packet_id=self.next_packet_id,
            source_ip=IPv4Address(source),
            destination_ip=IPv4Address(destination),
            protocol=protocol,
            payload=payload.encode("utf-8"),
            ttl=ttl,
            source_port=source_port,
            destination_port=destination_port,
        )

        self.next_packet_id += 1
        return packet

    def transmit(self, packet: Packet, source: str,
                 destination: str) -> dict:

        start = time.perf_counter()

        try:
            path = self.topology.shortest_path(source, destination)
            total_latency = 0.0
            bottleneck = float("inf")

            for index, current in enumerate(path):
                packet.hops.append(current)

                if index == len(path) - 1:
                    continue

                if not packet.decrement_ttl():
                    raise TimeoutError("Packet TTL expired")

                next_device = path[index + 1]

                link = next(
                    link for link in self.topology.adjacency[current]
                    if link.destination == next_device
                    and link.available
                )

                total_latency += link.latency_ms
                bottleneck = min(bottleneck, link.bandwidth_mbps)

            elapsed = (time.perf_counter() - start) * 1000
            self.delivered += 1
            self.transmitted_bytes += packet.size_bytes

            return {
                "packet_id": packet.packet_id,
                "status": "DELIVERED",
                "path": packet.hops,
                "ttl_remaining": packet.ttl,
                "latency_ms": round(total_latency, 3),
                "bottleneck_mbps": bottleneck,
                "packet_size_bytes": packet.size_bytes,
                "simulation_time_ms": round(elapsed, 3),
            }

        except (ConnectionError, TimeoutError, ValueError, StopIteration) as error:
            self.dropped += 1

            return {
                "packet_id": packet.packet_id,
                "status": "DROPPED",
                "reason": str(error),
                "path": packet.hops,
            }

    def statistics(self) -> dict:
        total = self.delivered + self.dropped

        return {
            "delivered": self.delivered,
            "dropped": self.dropped,
            "total": total,
            "delivery_ratio": (
                round(self.delivered / total * 100, 2)
                if total else 0
            ),
            "transmitted_bytes": self.transmitted_bytes,
        }


# ============================================================
# 8. NETWORK DEMONSTRATION
# ============================================================

def build_network() -> NetworkTopology:
    topology = NetworkTopology()

    devices = [
        NetworkDevice("PC1", "Development Computer", DeviceType.HOST),
        NetworkDevice("SW1", "Office Switch", DeviceType.SWITCH),
        NetworkDevice("R1", "Office Router", DeviceType.ROUTER),
        NetworkDevice("R2", "Remote Router", DeviceType.ROUTER),
        NetworkDevice("SW2", "Remote Switch", DeviceType.SWITCH),
        NetworkDevice("PC2", "Remote Server", DeviceType.HOST),
    ]

    for device in devices:
        topology.add_device(device)

    topology.connect(Link("PC1", "SW1", NetworkType.LAN, 1000, 0.1))
    topology.connect(Link("SW1", "R1", NetworkType.LAN, 1000, 0.2))
    topology.connect(Link("R1", "R2", NetworkType.WAN, 100, 20))
    topology.connect(Link("R2", "SW2", NetworkType.LAN, 1000, 0.2))
    topology.connect(Link("SW2", "PC2", NetworkType.LAN, 1000, 0.1))

    return topology


def run_tests() -> None:
    assert analyze_subnet("192.168.1.0/24")["usable_hosts"] == 254

    table = RoutingTable()
    table.add_route(Route(ip_network("10.0.0.0/8"), "R1"))
    table.add_route(Route(ip_network("10.1.0.0/16"), "R2"))

    assert table.lookup(IPv4Address("10.1.2.3")).next_hop == "R2"

    topology = build_network()
    engine = PacketSwitch(topology)

    packet = engine.create_packet(
        "192.168.1.10",
        "10.0.0.10",
        "Network connectivity test"
    )

    result = engine.transmit(packet, "PC1", "PC2")
    assert result["status"] == "DELIVERED"

    ttl_packet = engine.create_packet(
        "192.168.1.10",
        "10.0.0.10",
        "TTL test",
        ttl=2
    )

    assert engine.transmit(ttl_packet, "PC1", "PC2")["status"] == "DROPPED"

    print("\nAll validation tests passed.")


def main() -> None:
    print("=" * 65)
    print("INTRODUCTION TO COMPUTER NETWORKS")
    print("=" * 65)

    display_network_models()

    print("\nSUBNET ANALYSIS")
    print(json.dumps(
        analyze_subnet("192.168.1.0/24"),
        indent=4
    ))

    topology = build_network()
    engine = PacketSwitch(topology)

    print("\nPACKET SWITCHING")

    packet = engine.create_packet(
        "192.168.1.10",
        "10.0.0.10",
        "Hello from the local area network",
        Protocol.TCP,
        source_port=50000,
        destination_port=443,
    )

    print(json.dumps(
        engine.transmit(packet, "PC1", "PC2"),
        indent=4
    ))

    print("\nLINK FAILURE TEST")
    topology.set_link_status("R1", "R2", False)

    failed_packet = engine.create_packet(
        "192.168.1.10",
        "10.0.0.10",
        "Test during WAN failure"
    )

    print(json.dumps(
        engine.transmit(failed_packet, "PC1", "PC2"),
        indent=4
    ))

    print("\nNETWORK STATISTICS")
    print(json.dumps(engine.statistics(), indent=4))

    run_tests()


if __name__ == "__main__":
    main()
