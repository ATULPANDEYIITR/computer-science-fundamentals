#!/usr/bin/env python3
"""
Network Layer Engineering
IP addressing, IPv4, IPv6, subnetting, CIDR, routing and longest-prefix matching.

Python 3.10+
Standard library only.
"""

from __future__ import annotations

import ipaddress
import json
import logging
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger("network_layer")


class NetworkError(Exception):
    """Base exception for network operations."""


class AddressValidationError(NetworkError):
    pass


class RouteNotFoundError(NetworkError):
    pass


class AddressFamily(Enum):
    IPV4 = 4
    IPV6 = 6


class RouteStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


def parse_ip(value: str):
    """Parse an IPv4 or IPv6 address without performing DNS resolution."""
    try:
        return ipaddress.ip_address(value.strip())
    except (ValueError, AttributeError):
        raise AddressValidationError(
            f"Invalid IP address: {value}"
        )


def parse_network(value: str):
    """Parse a CIDR network and reject host bits in the network address."""
    try:
        return ipaddress.ip_network(value.strip(), strict=True)
    except (ValueError, AttributeError):
        raise AddressValidationError(
            f"Invalid CIDR network: {value}"
        )


@dataclass
class Interface:
    name: str
    address: str
    enabled: bool = True
    mtu: int = 1500

    def __post_init__(self):
        ip_interface = ipaddress.ip_interface(self.address)

        if not self.name:
            raise ValueError("Interface name cannot be empty")

        if not 576 <= self.mtu <= 65535:
            raise ValueError("MTU must be between 576 and 65535")

        self.address = str(ip_interface)

    @property
    def ip(self):
        return ipaddress.ip_interface(self.address).ip

    @property
    def network(self):
        return ipaddress.ip_interface(self.address).network

    def describe(self):
        return {
            "interface": self.name,
            "address": self.address,
            "network": str(self.network),
            "family": self.ip.version,
            "enabled": self.enabled,
            "mtu": self.mtu
        }


@dataclass
class Route:
    destination: str
    interface: str
    next_hop: Optional[str] = None
    metric: int = 100
    status: RouteStatus = RouteStatus.ACTIVE

    def __post_init__(self):
        network = parse_network(self.destination)

        if self.next_hop is not None:
            gateway = parse_ip(self.next_hop)

            if gateway.version != network.version:
                raise AddressValidationError(
                    "Gateway and destination address families differ"
                )

        if self.metric < 0:
            raise ValueError("Route metric cannot be negative")

        self.destination = str(network)


@dataclass
class RoutingTable:
    routes: list[Route] = field(default_factory=list)

    def add_route(self, route: Route):
        self.routes.append(route)

    def remove_route(self, destination: str, interface: str):
        before = len(self.routes)

        self.routes = [
            route for route in self.routes
            if not (
                route.destination == str(parse_network(destination))
                and route.interface == interface
            )
        ]

        return before - len(self.routes)

    def lookup(self, destination: str) -> Route:
        """
        Longest Prefix Match:
        1. Match address family.
        2. Find networks containing the destination.
        3. Select the longest prefix.
        4. Use the lowest metric for equal prefixes.
        """
        address = parse_ip(destination)

        candidates = []

        for route in self.routes:
            if route.status != RouteStatus.ACTIVE:
                continue

            network = parse_network(route.destination)

            if network.version != address.version:
                continue

            if address in network:
                candidates.append(route)

        if not candidates:
            raise RouteNotFoundError(
                f"No route to {address}"
            )

        return max(
            candidates,
            key=lambda route: (
                parse_network(route.destination).prefixlen,
                -route.metric
            )
        )

    def display(self):
        print("\nROUTING TABLE")
        print("-" * 80)

        for route in sorted(
            self.routes,
            key=lambda item: (
                ipaddress.ip_network(item.destination).version,
                -ipaddress.ip_network(item.destination).prefixlen
            )
        ):
            print(
                f"{route.destination:25} "
                f"{str(route.next_hop or 'direct'):18} "
                f"{route.interface:12} "
                f"metric={route.metric}"
            )


class NetworkManager:
    def __init__(self):
        self.interfaces: dict[str, Interface] = {}
        self.routing_table = RoutingTable()

    def add_interface(self, interface: Interface):
        if interface.name in self.interfaces:
            raise NetworkError(
                f"Interface already exists: {interface.name}"
            )

        self.interfaces[interface.name] = interface

    def add_route(self, route: Route):
        interface = self.interfaces.get(route.interface)

        if interface is None:
            raise NetworkError(
                f"Unknown interface: {route.interface}"
            )

        if not interface.enabled:
            raise NetworkError(
                f"Interface {route.interface} is disabled"
            )

        self.routing_table.add_route(route)

    def set_interface_state(self, name: str, enabled: bool):
        if name not in self.interfaces:
            raise NetworkError(f"Unknown interface: {name}")

        self.interfaces[name].enabled = enabled

    def route_packet(self, source: str, destination: str):
        source_ip = parse_ip(source)
        destination_ip = parse_ip(destination)

        if source_ip.version != destination_ip.version:
            raise NetworkError(
                "Source and destination address families differ"
            )

        route = self.routing_table.lookup(destination)

        interface = self.interfaces.get(route.interface)

        if interface is None or not interface.enabled:
            raise NetworkError(
                f"Outgoing interface {route.interface} unavailable"
            )

        if interface.ip.version != destination_ip.version:
            raise NetworkError(
                "Outgoing interface has incompatible address family"
            )

        if source_ip not in interface.network:
            logger.warning(
                "Source address is not configured on the outgoing interface"
            )

        return {
            "source": str(source_ip),
            "destination": str(destination_ip),
            "next_hop": route.next_hop or str(destination_ip),
            "interface": route.interface,
            "matched_network": route.destination,
            "prefix_length": parse_network(
                route.destination
            ).prefixlen,
            "metric": route.metric,
            "status": "forwarded"
        }


def subnet_analysis(cidr: str):
    """Calculate subnet properties for IPv4 or IPv6."""
    network = parse_network(cidr)

    result = {
        "network": str(network),
        "version": network.version,
        "prefix_length": network.prefixlen,
        "netmask": str(network.netmask),
        "broadcast": (
            str(network.broadcast_address)
            if network.version == 4 else None
        ),
        "total_addresses": network.num_addresses,
        "first_address": str(network.network_address),
        "last_address": str(network[-1]),
        "usable_ipv4_hosts": (
            max(0, network.num_addresses - 2)
            if network.version == 4 else None
        )
    }

    if network.version == 4 and network.prefixlen <= 30:
        result["first_usable"] = str(network.network_address + 1)
        result["last_usable"] = str(network.broadcast_address - 1)
    else:
        result["first_usable"] = str(network.network_address)
        result["last_usable"] = str(network[-1])

    return result


def split_subnets(cidr: str, new_prefix: int):
    """Divide a network into equal-sized subnets."""
    network = parse_network(cidr)

    if not network.prefixlen <= new_prefix <= network.max_prefixlen:
        raise ValueError("Invalid subnet prefix")

    return [
        str(subnet)
        for subnet in network.subnets(
            new_prefix=new_prefix
        )
    ]


def summarize_addresses(addresses: list[str]):
    """Aggregate adjacent addresses into minimal CIDR networks."""
    parsed = [parse_ip(address) for address in addresses]

    if not parsed:
        return []

    if len({address.version for address in parsed}) != 1:
        raise AddressValidationError(
            "Cannot summarize mixed IPv4 and IPv6 addresses"
        )

    return [
        str(network)
        for network in ipaddress.collapse_addresses(parsed)
    ]


def save_report(data: dict, filename: str):
    """Write JSON safely using UTF-8."""
    path = Path(filename)

    if path.suffix.lower() != ".json":
        raise ValueError("Report filename must end in .json")

    path.write_text(
        json.dumps(data, indent=4),
        encoding="utf-8"
    )


def run_examples():
    print("=" * 65)
    print("NETWORK LAYER ENGINEERING")
    print("=" * 65)

    # IPv4 subnet analysis.
    ipv4 = subnet_analysis("192.168.10.0/24")

    print("\nIPv4 SUBNET ANALYSIS")
    print(json.dumps(ipv4, indent=4))

    # IPv6 subnet analysis.
    ipv6 = subnet_analysis("2001:db8:100::/64")

    print("\nIPv6 SUBNET ANALYSIS")
    print(json.dumps(ipv6, indent=4))

    # Subnet division.
    print("\nSUBNET DIVISION")
    for subnet in split_subnets("192.168.10.0/24", 26):
        print(subnet)

    # Address summarization.
    print("\nADDRESS SUMMARIZATION")
    print(
        summarize_addresses([
            "192.168.1.0",
            "192.168.1.1",
            "192.168.1.2",
            "192.168.1.3"
        ])
    )

    # Build a dual-stack router.
    router = NetworkManager()

    router.add_interface(
        Interface("eth0", "192.168.10.1/24")
    )

    router.add_interface(
        Interface("eth1", "10.0.0.1/24")
    )

    router.add_interface(
        Interface("eth2", "2001:db8:1::1/64")
    )

    router.add_route(
        Route("192.168.10.0/24", "eth0")
    )

    router.add_route(
        Route("10.0.0.0/24", "eth1")
    )

    router.add_route(
        Route("172.16.0.0/16", "eth1", "10.0.0.2", 20)
    )

    router.add_route(
        Route("172.16.10.0/24", "eth1", "10.0.0.3", 10)
    )

    router.add_route(
        Route("2001:db8:1::/64", "eth2")
    )

    router.add_route(
        Route("2001:db8:2::/64", "eth2", "2001:db8:1::2")
    )

    router.routing_table.display()

    print("\nPACKET FORWARDING")
    result = router.route_packet(
        "192.168.10.20",
        "172.16.10.50"
    )

    print(json.dumps(result, indent=4))

    print("\nIPV6 FORWARDING")
    ipv6_result = router.route_packet(
        "2001:db8:1::10",
        "2001:db8:2::20"
    )

    print(json.dumps(ipv6_result, indent=4))

    # More-specific routes must take precedence.
    assert result["matched_network"] == "172.16.10.0/24"

    # Validation tests.
    print("\nVALIDATION TESTS")

    invalid_addresses = [
        "300.1.1.1",
        "192.168.1.256",
        "not-an-ip"
    ]

    for address in invalid_addresses:
        try:
            parse_ip(address)
        except AddressValidationError as error:
            print(f"Rejected {address}: {error}")

    try:
        router.routing_table.lookup("203.0.113.10")
    except RouteNotFoundError as error:
        print(f"Expected routing failure: {error}")

    # Interface failure.
    router.set_interface_state("eth1", False)

    try:
        router.route_packet(
            "192.168.10.20",
            "172.16.10.50"
        )
    except NetworkError as error:
        print(f"Expected interface failure: {error}")

    router.set_interface_state("eth1", True)

    # Verify IPv6 subnet calculations.
    assert ipv6["total_addresses"] == 2**64

    # Verify subnet count.
    assert len(
        split_subnets("192.168.10.0/24", 26)
    ) == 4

    print("\nALL ASSERTIONS PASSED")

    report = {
        "ipv4": ipv4,
        "ipv6": ipv6,
        "interfaces": [
            interface.describe()
            for interface in router.interfaces.values()
        ],
        "routes": [
            {
                "destination": route.destination,
                "interface": route.interface,
                "next_hop": route.next_hop,
                "metric": route.metric,
                "status": route.status.value
            }
            for route in router.routing_table.routes
        ]
    }

    save_report(report, "network_report.json")

    print("Report saved to network_report.json")


if __name__ == "__main__":
    run_examples()
