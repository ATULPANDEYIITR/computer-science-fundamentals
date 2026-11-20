"use strict";

/*
 * INTRODUCTION TO COMPUTER NETWORKS
 *
 * Event-driven network simulation using:
 * - LAN and WAN
 * - OSI and TCP/IP models
 * - IPv4 addressing
 * - Network devices
 * - Packet switching
 * - Routing and forwarding
 * - Asynchronous packet transmission
 * - Network events and monitoring
 *
 * Runtime: Node.js 18+
 */

const { EventEmitter } = require("node:events");
const { performance } = require("node:perf_hooks");
const net = require("node:net");
const assert = require("node:assert/strict");

// ============================================================
// 1. NETWORK MODELS
// ============================================================

const OSI_MODEL = Object.freeze([
    { layer: 1, name: "Physical", responsibility: "Bit transmission" },
    { layer: 2, name: "Data Link", responsibility: "Frames and MAC addresses" },
    { layer: 3, name: "Network", responsibility: "IP addressing and routing" },
    { layer: 4, name: "Transport", responsibility: "TCP and UDP communication" },
    { layer: 5, name: "Session", responsibility: "Session management" },
    { layer: 6, name: "Presentation", responsibility: "Encoding and encryption" },
    { layer: 7, name: "Application", responsibility: "Network applications" }
]);

const TCP_IP_MODEL = Object.freeze({
    Application: [5, 6, 7],
    Transport: [4],
    Internet: [3],
    "Network Access": [1, 2]
});

// ============================================================
// 2. IPV4 UTILITIES
// ============================================================

function ipv4ToNumber(address) {
    if (net.isIP(address) !== 4) {
        throw new TypeError(`Invalid IPv4 address: ${address}`);
    }

    return address.split(".").reduce(
        (result, part) => ((result * 256) + Number(part)) >>> 0,
        0
    );
}

function numberToIPv4(value) {
    return [
        (value >>> 24) & 255,
        (value >>> 16) & 255,
        (value >>> 8) & 255,
        value & 255
    ].join(".");
}

function parseCIDR(cidr) {
    const parts = cidr.split("/");

    if (parts.length !== 2) {
        throw new TypeError("CIDR must contain an address and prefix");
    }

    const address = ipv4ToNumber(parts[0]);
    const prefix = Number(parts[1]);

    if (!Number.isInteger(prefix) || prefix < 0 || prefix > 32) {
        throw new RangeError("Invalid IPv4 prefix");
    }

    const mask = prefix === 0
        ? 0
        : (0xFFFFFFFF << (32 - prefix)) >>> 0;

    const network = (address & mask) >>> 0;
    const broadcast = (network | (~mask >>> 0)) >>> 0;

    return Object.freeze({
        address: parts[0],
        prefix,
        mask: numberToIPv4(mask),
        network: numberToIPv4(network),
        broadcast: numberToIPv4(broadcast),
        totalAddresses: 2 ** (32 - prefix),
        contains(ip) {
            return (ipv4ToNumber(ip) & mask) >>> 0 === network;
        }
    });
}

// ============================================================
// 3. NETWORK DEVICES
// ============================================================

class NetworkDevice {
    constructor(id, name, type) {
        if (!id || !name) {
            throw new TypeError("Device ID and name are required");
        }

        if (!["HOST", "SWITCH", "ROUTER"].includes(type)) {
            throw new TypeError("Unsupported device type");
        }

        this.id = id;
        this.name = name;
        this.type = type;
        this.interfaces = new Map();
    }

    addInterface(name, ip, cidr, mac) {
        if (this.interfaces.has(name)) {
            throw new Error("Interface already exists");
        }

        if (net.isIP(ip) !== 4 || net.isIP(mac.replaceAll("-", ":")) !== 0) {
            // MAC addresses are validated separately.
            if (net.isIP(ip) !== 4) {
                throw new TypeError("Invalid interface IPv4 address");
            }
        }

        const normalizedMAC = mac.toUpperCase();

        if (!/^([0-9A-F]{2}:){5}[0-9A-F]{2}$/.test(normalizedMAC)) {
            throw new TypeError("Invalid MAC address");
        }

        const subnet = parseCIDR(cidr);

        if (!subnet.contains(ip)) {
            throw new Error("Interface IP does not belong to subnet");
        }

        this.interfaces.set(name, Object.freeze({
            name,
            ip,
            cidr,
            mac: normalizedMAC
        }));
    }
}

// ============================================================
// 4. PACKET MODEL
// ============================================================

let packetSequence = 1;

class Packet {
    constructor({
        source,
        destination,
        protocol = "TCP",
        payload,
        ttl = 64,
        sourcePort = null,
        destinationPort = null
    }) {
        ipv4ToNumber(source);
        ipv4ToNumber(destination);

        if (!["TCP", "UDP", "ICMP"].includes(protocol)) {
            throw new TypeError("Unsupported protocol");
        }

        if (!Number.isInteger(ttl) || ttl < 1 || ttl > 255) {
            throw new RangeError("TTL must be between 1 and 255");
        }

        if (typeof payload !== "string") {
            throw new TypeError("Payload must be a string");
        }

        if (Buffer.byteLength(payload) > 65507) {
            throw new RangeError("Payload exceeds simulation limit");
        }

        for (const port of [sourcePort, destinationPort]) {
            if (port !== null &&
                (!Number.isInteger(port) || port < 1 || port > 65535)) {
                throw new RangeError("Invalid transport port");
            }
        }

        this.id = packetSequence++;
        this.source = source;
        this.destination = destination;
        this.protocol = protocol;
        this.payload = Buffer.from(payload, "utf8");
        this.ttl = ttl;
        this.sourcePort = sourcePort;
        this.destinationPort = destinationPort;
        this.hops = [];

        Object.seal(this);
    }

    get sizeBytes() {
        const header = this.protocol === "TCP" ? 40 : 28;
        return header + this.payload.length;
    }

    forward(device) {
        this.hops.push(device);

        this.ttl--;

        if (this.ttl <= 0) {
            throw new Error("TTL_EXPIRED");
        }
    }
}

// ============================================================
// 5. NETWORK TOPOLOGY
// ============================================================

class NetworkTopology extends EventEmitter {
    constructor() {
        super();
        this.devices = new Map();
        this.links = new Map();
    }

    addDevice(device) {
        if (this.devices.has(device.id)) {
            throw new Error("Duplicate device");
        }

        this.devices.set(device.id, device);
        this.emit("deviceAdded", device);
    }

    connect(source, destination, {
        type,
        bandwidthMbps,
        latencyMs
    }) {
        if (!this.devices.has(source) ||
            !this.devices.has(destination)) {
            throw new Error("Unknown network device");
        }

        if (source === destination) {
            throw new Error("Self-links are not permitted");
        }

        if (!["LAN", "WAN"].includes(type)) {
            throw new TypeError("Invalid network type");
        }

        if (!Number.isFinite(bandwidthMbps) ||
            bandwidthMbps <= 0 ||
            !Number.isFinite(latencyMs) ||
            latencyMs < 0) {
            throw new RangeError("Invalid link parameters");
        }

        const key = `${source}->${destination}`;

        if (this.links.has(key)) {
            throw new Error("Duplicate link");
        }

        const link = {
            source,
            destination,
            type,
            bandwidthMbps,
            latencyMs,
            available: true
        };

        this.links.set(key, link);
        this.emit("linkConnected", link);
    }

    setLinkAvailability(source, destination, available) {
        const key = `${source}->${destination}`;
        const link = this.links.get(key);

        if (!link) {
            throw new Error("Link not found");
        }

        link.available = Boolean(available);
        this.emit("linkStatusChanged", link);
    }

    shortestPath(source, destination) {
        if (!this.devices.has(source) ||
            !this.devices.has(destination)) {
            throw new Error("Unknown endpoint");
        }

        const queue = [[source]];
        const visited = new Set([source]);

        while (queue.length > 0) {
            const path = queue.shift();
            const current = path[path.length - 1];

            if (current === destination) {
                return path;
            }

            for (const link of this.links.values()) {
                if (link.source !== current || !link.available) {
                    continue;
                }

                if (!visited.has(link.destination)) {
                    visited.add(link.destination);
                    queue.push([...path, link.destination]);
                }
            }
        }

        throw new Error("NO_ROUTE");
    }

    getLink(source, destination) {
        return this.links.get(`${source}->${destination}`);
    }
}

// ============================================================
// 6. ROUTING TABLE
// ============================================================

class RoutingTable {
    constructor() {
        this.routes = [];
    }

    add(network, nextHop, metric = 1) {
        const subnet = parseCIDR(network);

        if (!Number.isInteger(metric) || metric < 0) {
            throw new RangeError("Invalid route metric");
        }

        this.routes.push({ subnet, nextHop, metric });

        this.routes.sort(
            (a, b) =>
                b.subnet.prefix - a.subnet.prefix ||
                a.metric - b.metric
        );
    }

    lookup(destination) {
        return this.routes.find(
            route => route.subnet.contains(destination)
        ) || null;
    }
}

// ============================================================
// 7. ASYNCHRONOUS PACKET SWITCHING
// ============================================================

class PacketSwitch extends EventEmitter {
    constructor(topology) {
        super();
        this.topology = topology;
        this.statistics = {
            transmitted: 0,
            delivered: 0,
            dropped: 0,
            bytes: 0,
            latencyMs: 0
        };
    }

    async transmit(packet, source, destination) {
        const start = performance.now();

        this.statistics.transmitted++;
        this.emit("packetCreated", packet);

        try {
            const path = this.topology.shortestPath(source, destination);

            let latency = 0;
            let bandwidth = Infinity;

            for (let i = 0; i < path.length; i++) {
                const current = path[i];
                packet.hops.push(current);

                if (i === path.length - 1) {
                    break;
                }

                const next = path[i + 1];
                const link = this.topology.getLink(current, next);

                if (!link || !link.available) {
                    throw new Error("LINK_UNAVAILABLE");
                }

                packet.ttl--;

                if (packet.ttl <= 0) {
                    throw new Error("TTL_EXPIRED");
                }

                latency += link.latencyMs;
                bandwidth = Math.min(bandwidth, link.bandwidthMbps);

                // Asynchronous simulation of link transmission.
                await new Promise(resolve => setImmediate(resolve));
            }

            const result = {
                packetId: packet.id,
                status: "DELIVERED",
                path,
                latencyMs: latency,
                bottleneckMbps: bandwidth,
                ttlRemaining: packet.ttl,
                packetSizeBytes: packet.sizeBytes
            };

            this.statistics.delivered++;
            this.statistics.bytes += packet.sizeBytes;
            this.statistics.latencyMs += latency;

            this.emit("packetDelivered", result);
            return result;

        } catch (error) {
            this.statistics.dropped++;

            const result = {
                packetId: packet.id,
                status: "DROPPED",
                reason: error.message,
                path: [...packet.hops]
            };

            this.emit("packetDropped", result);
            return result;
        } finally {
            this.emit("transmissionCompleted", {
                packetId: packet.id,
                executionTimeMs: performance.now() - start
            });
        }
    }

    report() {
        const total = this.statistics.transmitted;

        return {
            ...this.statistics,
            deliveryRate: total
                ? this.statistics.delivered / total * 100
                : 0,
            averageLatencyMs: this.statistics.delivered
                ? this.statistics.latencyMs / this.statistics.delivered
                : 0
        };
    }
}

// ============================================================
// 8. NETWORK CONSTRUCTION
// ============================================================

function createNetwork() {
    const topology = new NetworkTopology();

    const definitions = [
        ["PC1", "Development Workstation", "HOST"],
        ["SW1", "Office Switch", "SWITCH"],
        ["R1", "Local Router", "ROUTER"],
        ["R2", "WAN Router", "ROUTER"],
        ["SW2", "Remote Switch", "SWITCH"],
        ["SRV1", "Remote Server", "HOST"]
    ];

    for (const [id, name, type] of definitions) {
        topology.addDevice(new NetworkDevice(id, name, type));
    }

    const connections = [
        ["PC1", "SW1", "LAN", 1000, 0.1],
        ["SW1", "R1", "LAN", 1000, 0.2],
        ["R1", "R2", "WAN", 100, 20],
        ["R2", "SW2", "LAN", 1000, 0.2],
        ["SW2", "SRV1", "LAN", 1000, 0.1]
    ];

    for (const [source, destination, type, bandwidth, latency] of connections) {
        topology.connect(source, destination, {
            type,
            bandwidthMbps: bandwidth,
            latencyMs: latency
        });
    }

    return topology;
}

// ============================================================
// 9. TESTING AND EXECUTION
// ============================================================

async function main() {
    console.log("INTRODUCTION TO COMPUTER NETWORKS\n");

    console.log("OSI MODEL");

    for (const layer of [...OSI_MODEL].reverse()) {
        console.log(
            `${layer.layer}. ${layer.name}: ${layer.responsibility}`
        );
    }

    console.log("\nTCP/IP MODEL");

    console.log(TCP_IP_MODEL);

    console.log("\nSUBNET ANALYSIS");

    const subnet = parseCIDR("192.168.1.10/24");

    console.log({
        network: subnet.network,
        broadcast: subnet.broadcast,
        mask: subnet.mask,
        totalAddresses: subnet.totalAddresses
    });

    assert.equal(subnet.contains("192.168.1.100"), true);
    assert.equal(subnet.contains("192.168.2.100"), false);

    const topology = createNetwork();

    topology.on("linkStatusChanged", link => {
        console.log(
            `Link ${link.source}->${link.destination}: ` +
            `${link.available ? "UP" : "DOWN"}`
        );
    });

    const switchEngine = new PacketSwitch(topology);

    switchEngine.on("packetDelivered", packet => {
        console.log(`Packet ${packet.packetId} delivered`);
    });

    switchEngine.on("packetDropped", packet => {
        console.log(`Packet ${packet.packetId} dropped: ${packet.reason}`);
    });

    console.log("\nPACKET TRANSMISSION");

    const packet = new Packet({
        source: "192.168.1.10",
        destination: "10.0.0.10",
        protocol: "TCP",
        payload: "Hello from the local network",
        sourcePort: 50000,
        destinationPort: 443
    });

    const result = await switchEngine.transmit(
        packet,
        "PC1",
        "SRV1"
    );

    console.log(result);

    assert.equal(result.status, "DELIVERED");

    console.log("\nTTL FAILURE");

    const ttlPacket = new Packet({
        source: "192.168.1.10",
        destination: "10.0.0.10",
        payload: "TTL test",
        ttl: 2
    });

    const ttlResult = await switchEngine.transmit(
        ttlPacket,
        "PC1",
        "SRV1"
    );

    assert.equal(ttlResult.status, "DROPPED");

    console.log(ttlResult);

    console.log("\nWAN FAILURE");

    topology.setLinkAvailability("R1", "R2", false);

    const failedPacket = new Packet({
        source: "192.168.1.10",
        destination: "10.0.0.10",
        payload: "WAN failure test"
    });

    const failedResult = await switchEngine.transmit(
        failedPacket,
        "PC1",
        "SRV1"
    );

    assert.equal(failedResult.status, "DROPPED");

    console.log(failedResult);

    console.log("\nROUTING TABLE");

    const routing = new RoutingTable();

    routing.add("10.0.0.0/8", "R1");
    routing.add("10.1.0.0/16", "R2");

    console.log(routing.lookup("10.1.2.3"));

    assert.equal(
        routing.lookup("10.1.2.3").nextHop,
        "R2"
    );

    console.log("\nNETWORK STATISTICS");
    console.log(switchEngine.report());

    console.log("\nAll tests passed.");
}

main().catch(error => {
    console.error("Network simulation failed:", error.message);
    process.exitCode = 1;
});
