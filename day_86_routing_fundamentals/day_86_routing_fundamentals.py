#!/usr/bin/env python3
"""
Routing Fundamentals
Static Routing, Dynamic Routing, Routing Tables, and Routing Algorithms.

Python 3.10+
Standard-library only.
"""

from __future__ import annotations

import heapq
import ipaddress
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("routing")


class RoutingError(Exception):
    """Base exception for routing operations."""


class RouteNotFoundError(RoutingError):
    """Raised when no route matches a destination."""


class ValidationError(RoutingError):
    """Raised when routing configuration is invalid."""


class RoutingProtocol(Enum):
    STATIC = "STATIC"
    RIP = "RIP"
    OSPF = "OSPF"


@dataclass(frozen=True)
class Link:
    destination: str
    cost: float
    available: bool = True

    def __post_init__(self):
        if not self.destination:
            raise ValidationError("Destination router cannot be empty.")
        if self.cost < 0:
            raise ValidationError("Link cost cannot be negative.")
        if not isinstance(self.cost, (int, float)):
            raise ValidationError("Link cost must be numeric.")


@dataclass
class Route:
    network: str
    next_hop: Optional[str]
    interface: str
    metric: float
    protocol: RoutingProtocol
    administrative_distance: int
    active: bool = True

    def __post_init__(self):
        try:
            ipaddress.ip_network(self.network, strict=False)
        except ValueError as exc:
            raise ValidationError(
                f"Invalid network: {self.network}"
            ) from exc

        if self.metric < 0:
            raise ValidationError("Route metric cannot be negative.")

        if self.administrative_distance < 0:
            raise ValidationError("Administrative distance cannot be negative.")


class RoutingTable:
    """Maintains routes and performs longest-prefix matching."""

    def __init__(self, router_id: str):
        self.router_id = router_id
        self.routes: list[Route] = []

    def add_route(self, route: Route) -> None:
        self.routes.append(route)
        logger.info(
            "%s installed route to %s through %s",
            self.router_id,
            route.network,
            route.next_hop
        )

    def remove_route(self, network: str, protocol=None) -> int:
        before = len(self.routes)
        self.routes = [
            route for route in self.routes
            if not (
                route.network == network
                and (protocol is None or route.protocol == protocol)
            )
        ]
        return before - len(self.routes)

    def lookup(self, destination: str) -> Route:
        try:
            address = ipaddress.ip_address(destination)
        except ValueError as exc:
            raise ValidationError(
                f"Invalid destination address: {destination}"
            ) from exc

        candidates = []

        for route in self.routes:
            if not route.active:
                continue

            network = ipaddress.ip_network(
                route.network,
                strict=False
            )

            if address.version == network.version and address in network:
                candidates.append(route)

        if not candidates:
            raise RouteNotFoundError(
                f"No route found for {destination}"
            )

        # Longest prefix wins; administrative distance and metric
        # resolve competing routes for the same prefix.
        return min(
            candidates,
            key=lambda route: (
                -ipaddress.ip_network(
                    route.network, strict=False
                ).prefixlen,
                route.administrative_distance,
                route.metric
            )
        )

    def display(self) -> None:
        print(f"\nRouting table: {self.router_id}")
        print(
            f"{'Network':<20} {'Next Hop':<15} "
            f"{'Interface':<12} {'Metric':<8} {'Protocol':<10}"
        )
        print("-" * 75)

        for route in sorted(
            self.routes,
            key=lambda r: (
                r.network,
                r.administrative_distance,
                r.metric
            )
        ):
            if route.active:
                print(
                    f"{route.network:<20} "
                    f"{str(route.next_hop or 'DIRECT'):<15} "
                    f"{route.interface:<12} "
                    f"{route.metric:<8} "
                    f"{route.protocol.value:<10}"
                )


class Network:
    """Represents a network topology using an adjacency list."""

    def __init__(self):
        self.graph: dict[str, list[Link]] = {}

    def add_router(self, router: str) -> None:
        if not router:
            raise ValidationError("Router name cannot be empty.")
        self.graph.setdefault(router, [])

    def add_link(
        self,
        source: str,
        destination: str,
        cost: float,
        bidirectional: bool = True
    ) -> None:
        if source == destination:
            raise ValidationError("Self-links are not supported.")

        if cost < 0:
            raise ValidationError("Link cost cannot be negative.")

        self.add_router(source)
        self.add_router(destination)

        self.graph[source] = [
            link for link in self.graph[source]
            if link.destination != destination
        ]

        self.graph[source].append(
            Link(destination, cost)
        )

        if bidirectional:
            self.add_link(
                destination,
                source,
                cost,
                bidirectional=False
            )

    def set_link_state(
        self,
        source: str,
        destination: str,
        available: bool
    ) -> None:
        if source not in self.graph:
            raise ValidationError(f"Unknown router: {source}")

        updated = False
        links = []

        for link in self.graph[source]:
            if link.destination == destination:
                links.append(
                    Link(destination, link.cost, available)
                )
                updated = True
            else:
                links.append(link)

        if not updated:
            raise ValidationError("Link does not exist.")

        self.graph[source] = links

    def neighbors(self, router: str) -> list[Link]:
        if router not in self.graph:
            raise ValidationError(f"Unknown router: {router}")

        return [
            link for link in self.graph[router]
            if link.available
        ]


class DijkstraRouter:
    """Shortest-path routing using Dijkstra's algorithm."""

    @staticmethod
    def calculate(
        network: Network,
        source: str
    ) -> dict[str, tuple[float, Optional[str]]]:

        if source not in network.graph:
            raise ValidationError("Source router does not exist.")

        distances = {
            router: float("inf")
            for router in network.graph
        }
        first_hop = {
            router: None
            for router in network.graph
        }

        distances[source] = 0
        queue = [(0, source)]

        while queue:
            current_cost, current = heapq.heappop(queue)

            if current_cost > distances[current]:
                continue

            for link in network.neighbors(current):
                new_cost = current_cost + link.cost

                if new_cost < distances[link.destination]:
                    distances[link.destination] = new_cost

                    first_hop[link.destination] = (
                        link.destination
                        if current == source
                        else first_hop[current]
                    )

                    heapq.heappush(
                        queue,
                        (new_cost, link.destination)
                    )

        return {
            router: (distances[router], first_hop[router])
            for router in network.graph
        }


class DistanceVectorRouter:
    """Bellman-Ford-style iterative distance-vector calculation."""

    @staticmethod
    def calculate(
        network: Network,
        source: str,
        max_iterations: int = 100
    ) -> dict[str, tuple[float, Optional[str]]]:

        if source not in network.graph:
            raise ValidationError("Source router does not exist.")

        if max_iterations < 1:
            raise ValidationError("Iterations must be positive.")

        distances = {
            router: float("inf")
            for router in network.graph
        }
        next_hops = {
            router: None
            for router in network.graph
        }

        distances[source] = 0

        # Each iteration propagates information by at most one edge.
        for _ in range(max_iterations):
            changed = False

            for router in network.graph:
                for link in network.neighbors(router):
                    if distances[router] == float("inf"):
                        continue

                    candidate = distances[router] + link.cost

                    if candidate < distances[link.destination]:
                        distances[link.destination] = candidate
                        next_hops[link.destination] = (
                            link.destination
                            if router == source
                            else next_hops[router]
                        )
                        changed = True

            if not changed:
                break

        return {
            router: (distances[router], next_hops[router])
            for router in network.graph
        }


class RoutingSimulator:
    """Combines topology, route installation, and packet forwarding."""

    ADMINISTRATIVE_DISTANCES = {
        RoutingProtocol.STATIC: 1,
        RoutingProtocol.OSPF: 110,
        RoutingProtocol.RIP: 120
    }

    def __init__(self):
        self.network = Network()
        self.tables: dict[str, RoutingTable] = {}

    def add_router(self, router: str) -> None:
        self.network.add_router(router)
        self.tables.setdefault(router, RoutingTable(router))

    def add_link(self, *args, **kwargs) -> None:
        self.network.add_link(*args, **kwargs)

    def install_static_route(
        self,
        router: str,
        network: str,
        next_hop: Optional[str],
        interface: str,
        metric: float = 1
    ) -> None:

        if router not in self.tables:
            raise ValidationError("Unknown router.")

        if next_hop is not None:
            if next_hop not in self.network.graph:
                raise ValidationError("Next-hop router does not exist.")

        self.tables[router].add_route(
            Route(
                network=network,
                next_hop=next_hop,
                interface=interface,
                metric=metric,
                protocol=RoutingProtocol.STATIC,
                administrative_distance=1
            )
        )

    def install_dynamic_routes(
        self,
        router: str,
        destinations: dict[str, str],
        protocol: RoutingProtocol = RoutingProtocol.OSPF
    ) -> None:

        if router not in self.tables:
            raise ValidationError("Unknown router.")

        if protocol not in (
            RoutingProtocol.OSPF,
            RoutingProtocol.RIP
        ):
            raise ValidationError("Invalid dynamic routing protocol.")

        if protocol == RoutingProtocol.OSPF:
            results = DijkstraRouter.calculate(
                self.network, router
            )
        else:
            results = DistanceVectorRouter.calculate(
                self.network, router
            )

        for destination, network in destinations.items():
            cost, next_hop = results[destination]

            if cost == float("inf"):
                continue

            self.tables[router].add_route(
                Route(
                    network=network,
                    next_hop=next_hop,
                    interface=f"eth-{next_hop}",
                    metric=cost,
                    protocol=protocol,
                    administrative_distance=(
                        self.ADMINISTRATIVE_DISTANCES[protocol]
                    )
                )
            )

    def forward_packet(
        self,
        router: str,
        destination_ip: str
    ) -> dict:

        if router not in self.tables:
            raise ValidationError("Unknown router.")

        route = self.tables[router].lookup(destination_ip)

        return {
            "router": router,
            "destination": destination_ip,
            "network": route.network,
            "next_hop": route.next_hop or "DIRECT",
            "interface": route.interface,
            "protocol": route.protocol.value,
            "metric": route.metric
        }


def demonstrate_routing() -> None:
    simulator = RoutingSimulator()

    for router in ["R1", "R2", "R3", "R4"]:
        simulator.add_router(router)

    simulator.add_link("R1", "R2", 2)
    simulator.add_link("R1", "R3", 5)
    simulator.add_link("R2", "R3", 1)
    simulator.add_link("R2", "R4", 7)
    simulator.add_link("R3", "R4", 2)

    print("\n1. DIJKSTRA SHORTEST PATHS")
    paths = DijkstraRouter.calculate(
        simulator.network, "R1"
    )

    for router, (cost, hop) in paths.items():
        print(
            f"R1 -> {router}: cost={cost}, "
            f"next_hop={hop or 'LOCAL'}"
        )

    print("\n2. DISTANCE VECTOR ROUTING")
    vectors = DistanceVectorRouter.calculate(
        simulator.network, "R1"
    )

    for router, (cost, hop) in vectors.items():
        print(
            f"R1 -> {router}: cost={cost}, "
            f"next_hop={hop or 'LOCAL'}"
        )

    print("\n3. STATIC ROUTING")
    simulator.install_static_route(
        "R1",
        "192.168.10.0/24",
        "R2",
        "eth0"
    )

    print(
        simulator.forward_packet(
            "R1", "192.168.10.25"
        )
    )

    print("\n4. DYNAMIC OSPF ROUTING")
    simulator.install_dynamic_routes(
        "R1",
        {
            "R2": "10.0.2.0/24",
            "R3": "10.0.3.0/24",
            "R4": "10.0.4.0/24"
        },
        RoutingProtocol.OSPF
    )

    simulator.tables["R1"].display()

    print("\n5. LINK FAILURE")
    simulator.network.set_link_state(
        "R2", "R3", False
    )

    updated = DijkstraRouter.calculate(
        simulator.network, "R1"
    )

    for router, (cost, hop) in updated.items():
        print(
            f"R1 -> {router}: cost={cost}, "
            f"next_hop={hop}"
        )

    print("\n6. LONGEST PREFIX MATCHING")
    table = RoutingTable("R5")

    table.add_route(
        Route(
            "192.168.0.0/16",
            "R2",
            "eth0",
            10,
            RoutingProtocol.STATIC,
            1
        )
    )

    table.add_route(
        Route(
            "192.168.10.0/24",
            "R3",
            "eth1",
            5,
            RoutingProtocol.OSPF,
            110
        )
    )

    print(
        "Selected route:",
        table.lookup("192.168.10.50")
    )

    print("\n7. ERROR HANDLING")

    try:
        table.lookup("172.16.0.10")
    except RoutingError as exc:
        logger.warning("%s", exc)

    try:
        simulator.install_static_route(
            "R1",
            "invalid-network",
            "R2",
            "eth0"
        )
    except ValidationError as exc:
        logger.warning("%s", exc)


def run_tests() -> None:
    network = Network()

    for router in ["A", "B", "C"]:
        network.add_router(router)

    network.add_link("A", "B", 2)
    network.add_link("B", "C", 3)
    network.add_link("A", "C", 10)

    dijkstra = DijkstraRouter.calculate(network, "A")
    distance_vector = DistanceVectorRouter.calculate(
        network, "A"
    )

    assert dijkstra["C"][0] == 5
    assert distance_vector["C"][0] == 5
    assert dijkstra["C"][1] == "B"

    table = RoutingTable("A")

    table.add_route(
        Route(
            "10.0.0.0/8",
            "B",
            "eth0",
            10,
            RoutingProtocol.STATIC,
            1
        )
    )

    table.add_route(
        Route(
            "10.1.0.0/16",
            "C",
            "eth1",
            5,
            RoutingProtocol.OSPF,
            110
        )
    )

    assert table.lookup("10.1.2.3").network == "10.1.0.0/16"
    assert table.lookup("10.2.2.3").network == "10.0.0.0/8"

    network.set_link_state("B", "C", False)

    updated = DijkstraRouter.calculate(network, "A")
    assert updated["C"][0] == 10

    print("\nAll routing tests passed.")


if __name__ == "__main__":
    demonstrate_routing()
    run_tests()
