"use strict";

/*
 * Routing Fundamentals
 * Event-driven routing simulation using Node.js.
 * Static routes, routing tables, OSPF-style shortest paths,
 * distance-vector updates, failure detection and forwarding.
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");

class RoutingError extends Error {}
class ValidationError extends RoutingError {}
class RouteNotFoundError extends RoutingError {}

const Protocol = Object.freeze({
    STATIC: "STATIC",
    OSPF: "OSPF",
    RIP: "RIP"
});

const ADMIN_DISTANCE = Object.freeze({
    STATIC: 1,
    OSPF: 110,
    RIP: 120
});

function validateRouterId(id) {
    if (
        typeof id !== "string" ||
        !/^[A-Za-z0-9_-]{1,32}$/.test(id)
    ) {
        throw new ValidationError(
            `Invalid router identifier: ${id}`
        );
    }
}

function validateNetwork(cidr) {
    if (typeof cidr !== "string") {
        throw new ValidationError("Network must be a string.");
    }

    const match = cidr.match(
        /^(\d{1,3}(?:\.\d{1,3}){3})\/(\d{1,2})$/
    );

    if (!match) {
        throw new ValidationError(`Invalid IPv4 CIDR: ${cidr}`);
    }

    const octets = match[1].split(".").map(Number);
    const prefix = Number(match[2]);

    if (
        octets.some(value => value < 0 || value > 255) ||
        prefix < 0 ||
        prefix > 32
    ) {
        throw new ValidationError(`Invalid network: ${cidr}`);
    }

    const address = octets.reduce(
        (result, octet) => result * 256 + octet,
        0
    );

    const mask = prefix === 0
        ? 0
        : (0xFFFFFFFF << (32 - prefix)) >>> 0;

    return {
        cidr,
        prefix,
        network: (address & mask) >>> 0
    };
}

function ipv4ToInteger(address) {
    const octets = address.split(".");

    if (
        octets.length !== 4 ||
        octets.some(
            part => !/^\d{1,3}$/.test(part) ||
            Number(part) > 255
        )
    ) {
        throw new ValidationError(
            `Invalid IPv4 address: ${address}`
        );
    }

    return octets.reduce(
        (result, part) =>
            (result * 256 + Number(part)) >>> 0,
        0
    );
}

function containsAddress(cidr, address) {
    const network = validateNetwork(cidr);
    const ip = ipv4ToInteger(address);

    const mask = network.prefix === 0
        ? 0
        : (0xFFFFFFFF << (32 - network.prefix)) >>> 0;

    return ((ip & mask) >>> 0) === network.network;
}

class RoutingTable {
    #routes = new Map();

    constructor(routerId) {
        validateRouterId(routerId);
        this.routerId = routerId;
    }

    add(route) {
        const network = validateNetwork(route.network);

        if (!Object.values(Protocol).includes(route.protocol)) {
            throw new ValidationError("Unknown routing protocol.");
        }

        if (
            !Number.isFinite(route.metric) ||
            route.metric < 0
        ) {
            throw new ValidationError("Invalid route metric.");
        }

        if (
            !Number.isInteger(route.administrativeDistance) ||
            route.administrativeDistance < 0
        ) {
            throw new ValidationError(
                "Invalid administrative distance."
            );
        }

        const normalized = Object.freeze({
            ...route,
            prefix: network.prefix,
            active: route.active !== false
        });

        const key = `${route.network}:${route.protocol}`;

        this.#routes.set(key, normalized);

        return normalized;
    }

    remove(network, protocol) {
        return this.#routes.delete(`${network}:${protocol}`);
    }

    lookup(destination) {
        ipv4ToInteger(destination);

        const matches = [...this.#routes.values()]
            .filter(route =>
                route.active &&
                containsAddress(route.network, destination)
            )
            .sort((a, b) =>
                b.prefix - a.prefix ||
                a.administrativeDistance -
                    b.administrativeDistance ||
                a.metric - b.metric
            );

        if (matches.length === 0) {
            throw new RouteNotFoundError(
                `No route to ${destination}`
            );
        }

        return matches[0];
    }

    getAll() {
        return [...this.#routes.values()];
    }
}

class NetworkTopology extends EventEmitter {
    #adjacency = new Map();

    addRouter(id) {
        validateRouterId(id);

        if (!this.#adjacency.has(id)) {
            this.#adjacency.set(id, new Map());
            this.emit("routerAdded", { router: id });
        }
    }

    addLink(source, destination, cost, bidirectional = true) {
        validateRouterId(source);
        validateRouterId(destination);

        if (source === destination) {
            throw new ValidationError("Self-links are invalid.");
        }

        if (!Number.isFinite(cost) || cost < 0) {
            throw new ValidationError(
                "Link cost must be non-negative."
            );
        }

        this.addRouter(source);
        this.addRouter(destination);

        this.#adjacency.get(source).set(destination, {
            cost,
            available: true
        });

        if (bidirectional) {
            this.addLink(
                destination,
                source,
                cost,
                false
            );
        }

        this.emit("topologyChanged", {
            source,
            destination,
            cost
        });
    }

    setLinkState(source, destination, available) {
        const links = this.#adjacency.get(source);

        if (!links || !links.has(destination)) {
            throw new ValidationError("Link does not exist.");
        }

        links.get(destination).available = Boolean(available);

        this.emit("linkStateChanged", {
            source,
            destination,
            available: Boolean(available)
        });
    }

    getRouters() {
        return [...this.#adjacency.keys()];
    }

    getNeighbors(router) {
        const links = this.#adjacency.get(router);

        if (!links) {
            throw new ValidationError("Unknown router.");
        }

        return [...links.entries()]
            .filter(([, link]) => link.available)
            .map(([destination, link]) => ({
                destination,
                cost: link.cost
            }));
    }
}

class ShortestPathEngine {
    static dijkstra(topology, source) {
        const routers = topology.getRouters();

        if (!routers.includes(source)) {
            throw new ValidationError("Unknown source router.");
        }

        const distances = new Map();
        const nextHops = new Map();
        const visited = new Set();

        for (const router of routers) {
            distances.set(router, Infinity);
            nextHops.set(router, null);
        }

        distances.set(source, 0);

        // A binary heap is used to avoid repeatedly sorting all routers.
        const heap = [{
            router: source,
            distance: 0
        }];

        while (heap.length > 0) {
            heap.sort((a, b) => b.distance - a.distance);

            const current = heap.pop();

            if (visited.has(current.router)) {
                continue;
            }

            visited.add(current.router);

            if (
                current.distance >
                distances.get(current.router)
            ) {
                continue;
            }

            for (const edge of topology.getNeighbors(current.router)) {
                const candidate =
                    current.distance + edge.cost;

                if (candidate < distances.get(edge.destination)) {
                    distances.set(edge.destination, candidate);

                    nextHops.set(
                        edge.destination,
                        current.router === source
                            ? edge.destination
                            : nextHops.get(current.router)
                    );

                    heap.push({
                        router: edge.destination,
                        distance: candidate
                    });
                }
            }
        }

        return new Map(
            routers.map(router => [
                router,
                {
                    cost: distances.get(router),
                    nextHop: nextHops.get(router)
                }
            ])
        );
    }

    static distanceVector(topology, source) {
        const routers = topology.getRouters();

        if (!routers.includes(source)) {
            throw new ValidationError("Unknown source router.");
        }

        const distances = new Map(
            routers.map(router => [router, Infinity])
        );

        const nextHops = new Map(
            routers.map(router => [router, null])
        );

        distances.set(source, 0);

        // Synchronous snapshots prevent update-order dependence.
        for (let iteration = 0; iteration < routers.length - 1; iteration++) {
            const previous = new Map(distances);
            const previousHops = new Map(nextHops);
            let changed = false;

            for (const router of routers) {
                if (previous.get(router) === Infinity) {
                    continue;
                }

                for (const edge of topology.getNeighbors(router)) {
                    const candidate =
                        previous.get(router) + edge.cost;

                    if (candidate < distances.get(edge.destination)) {
                        distances.set(edge.destination, candidate);

                        nextHops.set(
                            edge.destination,
                            router === source
                                ? edge.destination
                                : previousHops.get(router)
                        );

                        changed = true;
                    }
                }
            }

            if (!changed) break;
        }

        return new Map(
            routers.map(router => [
                router,
                {
                    cost: distances.get(router),
                    nextHop: nextHops.get(router)
                }
            ])
        );
    }
}

class Router {
    constructor(id, topology) {
        this.id = id;
        this.topology = topology;
        this.table = new RoutingTable(id);
    }

    installStaticRoute(network, nextHop, interfaceName, metric = 1) {
        if (nextHop !== null &&
            !this.topology.getRouters().includes(nextHop)) {
            throw new ValidationError("Unknown next-hop router.");
        }

        return this.table.add({
            network,
            nextHop,
            interface: interfaceName,
            metric,
            protocol: Protocol.STATIC,
            administrativeDistance: ADMIN_DISTANCE.STATIC
        });
    }

    installDynamicRoutes(destinationNetworks, protocol) {
        if (![Protocol.OSPF, Protocol.RIP].includes(protocol)) {
            throw new ValidationError(
                "Dynamic protocol must be OSPF or RIP."
            );
        }

        const results = protocol === Protocol.OSPF
            ? ShortestPathEngine.dijkstra(this.topology, this.id)
            : ShortestPathEngine.distanceVector(
                this.topology,
                this.id
            );

        const installed = [];

        for (const [router, network] of Object.entries(
            destinationNetworks
        )) {
            const result = results.get(router);

            if (!result || !Number.isFinite(result.cost)) {
                continue;
            }

            installed.push(this.table.add({
                network,
                nextHop: result.nextHop,
                interface: `eth-${result.nextHop}`,
                metric: result.cost,
                protocol,
                administrativeDistance: ADMIN_DISTANCE[protocol]
            }));
        }

        return installed;
    }

    forward(destination) {
        const route = this.table.lookup(destination);

        return {
            router: this.id,
            destination,
            network: route.network,
            nextHop: route.nextHop ?? "DIRECT",
            interface: route.interface,
            protocol: route.protocol,
            metric: route.metric
        };
    }
}

class RoutingController extends EventEmitter {
    constructor() {
        super();

        this.topology = new NetworkTopology();
        this.routers = new Map();

        this.topology.on("linkStateChanged", event => {
            this.emit("recalculationRequired", event);
        });
    }

    addRouter(id) {
        this.topology.addRouter(id);

        if (!this.routers.has(id)) {
            this.routers.set(
                id,
                new Router(id, this.topology)
            );
        }

        return this.routers.get(id);
    }

    addLink(...args) {
        this.topology.addLink(...args);
    }

    getRouter(id) {
        const router = this.routers.get(id);

        if (!router) {
            throw new ValidationError(`Unknown router: ${id}`);
        }

        return router;
    }

    async exportTable(routerId, filePath) {
        const router = this.getRouter(routerId);

        const content = JSON.stringify(
            router.table.getAll(),
            null,
            2
        );

        // Exclusive creation prevents accidental overwriting.
        await fs.writeFile(filePath, content, {
            encoding: "utf8",
            flag: "wx",
            mode: 0o600
        });
    }
}

async function main() {
    const controller = new RoutingController();

    controller.on("recalculationRequired", event => {
        console.log(
            "Topology changed. Recalculation required:",
            event
        );
    });

    for (const id of ["R1", "R2", "R3", "R4"]) {
        controller.addRouter(id);
    }

    controller.addLink("R1", "R2", 2);
    controller.addLink("R1", "R3", 5);
    controller.addLink("R2", "R3", 1);
    controller.addLink("R2", "R4", 7);
    controller.addLink("R3", "R4", 2);

    console.log("\nDIJKSTRA ROUTING");

    const ospf = ShortestPathEngine.dijkstra(
        controller.topology,
        "R1"
    );

    console.table(
        [...ospf.entries()].map(([router, result]) => ({
            router,
            cost: result.cost,
            nextHop: result.nextHop
        }))
    );

    console.log("\nDISTANCE VECTOR ROUTING");

    const rip = ShortestPathEngine.distanceVector(
        controller.topology,
        "R1"
    );

    console.table(
        [...rip.entries()].map(([router, result]) => ({
            router,
            cost: result.cost,
            nextHop: result.nextHop
        }))
    );

    const r1 = controller.getRouter("R1");

    console.log("\nSTATIC ROUTE");

    r1.installStaticRoute(
        "192.168.10.0/24",
        "R2",
        "eth0"
    );

    console.log(
        r1.forward("192.168.10.25")
    );

    console.log("\nDYNAMIC OSPF ROUTES");

    r1.installDynamicRoutes({
        R2: "10.0.2.0/24",
        R3: "10.0.3.0/24",
        R4: "10.0.4.0/24"
    }, Protocol.OSPF);

    console.table(r1.table.getAll());

    console.log("\nLINK FAILURE");

    controller.topology.setLinkState(
        "R2",
        "R3",
        false
    );

    const updated = ShortestPathEngine.dijkstra(
        controller.topology,
        "R1"
    );

    console.log("New path to R4:", updated.get("R4"));

    console.log("\nVALIDATION AND ERROR HANDLING");

    try {
        r1.forward("172.16.0.10");
    } catch (error) {
        if (error instanceof RoutingError) {
            console.error(error.message);
        } else {
            throw error;
        }
    }

    try {
        validateNetwork("300.0.0.0/24");
    } catch (error) {
        console.error(error.message);
    }

    console.log("\nROUTING TESTS");

    if (ospf.get("R4").cost !== 5) {
        throw new Error("Unexpected shortest path.");
    }

    if (rip.get("R4").cost !== 5) {
        throw new Error("Unexpected distance vector.");
    }

    if (updated.get("R4").cost !== 9) {
        throw new Error("Link failure calculation incorrect.");
    }

    console.log("All tests passed.");
}

main().catch(error => {
    console.error("Fatal routing error:", error.message);
    process.exitCode = 1;
});
