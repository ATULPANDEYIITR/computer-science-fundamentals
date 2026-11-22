"use strict";

/*
 * TCP/IP Model: Event-Driven Network Communication Simulator
 *
 * Node.js 18+
 *
 * Features:
 * - Four-layer TCP/IP architecture
 * - Protocol registry
 * - Asynchronous DNS resolution
 * - Event-driven packet transmission
 * - TCP connection state management
 * - UDP datagram processing
 * - IPv4 routing and longest-prefix matching
 * - Encapsulation and decapsulation
 * - Network MTU validation
 * - Packet inspection and diagnostics
 *
 * Run: node tcpip.js
 */

const { EventEmitter } = require("node:events");
const net = require("node:net");
const crypto = require("node:crypto");

// ============================================================
// 1. ARCHITECTURE AND PROTOCOL REGISTRY
// ============================================================

const Layers = Object.freeze({
    APPLICATION: 4,
    TRANSPORT: 3,
    INTERNET: 2,
    NETWORK_ACCESS: 1
});

const ProtocolRegistry = new Map([
    ["HTTP", { layer: Layers.APPLICATION, port: 80 }],
    ["HTTPS", { layer: Layers.APPLICATION, port: 443 }],
    ["DNS", { layer: Layers.APPLICATION, port: 53 }],
    ["DHCP", { layer: Layers.APPLICATION, port: 67 }],
    ["TCP", { layer: Layers.TRANSPORT, number: 6 }],
    ["UDP", { layer: Layers.TRANSPORT, number: 17 }],
    ["ICMP", { layer: Layers.INTERNET, number: 1 }],
    ["IPv4", { layer: Layers.INTERNET, number: 4 }],
    ["Ethernet", { layer: Layers.NETWORK_ACCESS, type: 0x0800 }]
]);

function displayArchitecture() {
    const architecture = [
        ["Application", "HTTP, HTTPS, DNS, DHCP, SMTP"],
        ["Transport", "TCP, UDP, ports, segmentation"],
        ["Internet", "IPv4, ICMP, routing"],
        ["Network Access", "Ethernet, MAC, framing"]
    ];

    console.log("\nTCP/IP ARCHITECTURE");

    architecture.forEach(([name, protocols]) => {
        console.log(`${name}: ${protocols}`);
    });
}

// ============================================================
// 2. VALIDATION
// ============================================================

class NetworkError extends Error {}
class RoutingError extends NetworkError {}
class ProtocolError extends NetworkError {}
class StateTransitionError extends NetworkError {}

function validateIPv4(address) {
    if (net.isIP(address) !== 4) {
        throw new TypeError(`Invalid IPv4 address: ${address}`);
    }

    return address;
}

function validatePort(port) {
    if (!Number.isInteger(port) || port < 1 || port > 65535) {
        throw new RangeError(`Invalid port: ${port}`);
    }

    return port;
}

function ipv4ToInteger(address) {
    validateIPv4(address);

    return address.split(".").reduce(
        (result, octet) => ((result << 8) | Number(octet)) >>> 0,
        0
    );
}

// ============================================================
// 3. CIDR NETWORK
// ============================================================

class IPv4Network {
    constructor(cidr) {
        const parts = cidr.split("/");

        if (parts.length !== 2) {
            throw new TypeError("CIDR notation is required.");
        }

        const [address, prefixText] = parts;
        const prefix = Number(prefixText);

        validateIPv4(address);

        if (!Number.isInteger(prefix) || prefix < 0 || prefix > 32) {
            throw new RangeError("Invalid subnet prefix.");
        }

        this.prefix = prefix;

        this.mask = prefix === 0
            ? 0
            : (0xFFFFFFFF << (32 - prefix)) >>> 0;

        this.network = ipv4ToInteger(address) & this.mask;
        this.cidr = `${this.toAddress(this.network)}/${prefix}`;
    }

    toAddress(value) {
        return [
            (value >>> 24) & 255,
            (value >>> 16) & 255,
            (value >>> 8) & 255,
            value & 255
        ].join(".");
    }

    contains(address) {
        return (
            (ipv4ToInteger(address) & this.mask) === this.network
        );
    }

    get broadcast() {
        return this.toAddress(
            (this.network | (~this.mask >>> 0)) >>> 0
        );
    }
}

// ============================================================
// 4. APPLICATION LAYER
// ============================================================

class ApplicationMessage {
    constructor(protocol, content) {
        if (!ProtocolRegistry.has(protocol)) {
            throw new ProtocolError("Unknown protocol.");
        }

        const definition = ProtocolRegistry.get(protocol);

        if (definition.layer !== Layers.APPLICATION) {
            throw new ProtocolError(
                "Protocol does not belong to application layer."
            );
        }

        if (typeof content !== "string" || content.length === 0) {
            throw new TypeError("Application content is required.");
        }

        this.protocol = protocol;
        this.payload = Buffer.from(content, "utf8");
        this.createdAt = new Date();
    }
}

// ============================================================
// 5. TRANSPORT LAYER: TCP
// ============================================================

const TCPStates = Object.freeze({
    CLOSED: "CLOSED",
    SYN_SENT: "SYN_SENT",
    SYN_RECEIVED: "SYN_RECEIVED",
    ESTABLISHED: "ESTABLISHED",
    FIN_WAIT: "FIN_WAIT",
    TIME_WAIT: "TIME_WAIT"
});

class TCPConnection extends EventEmitter {
    #state = TCPStates.CLOSED;

    constructor(sourcePort, destinationPort) {
        super();

        this.sourcePort = validatePort(sourcePort);
        this.destinationPort = validatePort(destinationPort);

        this.sequenceNumber = crypto.randomInt(0, 0x7FFFFFFF);
        this.acknowledgmentNumber = 0;
    }

    get state() {
        return this.#state;
    }

    transition(expected, next) {
        if (this.#state !== expected) {
            throw new StateTransitionError(
                `Expected ${expected}, found ${this.#state}`
            );
        }

        this.#state = next;

        this.emit("stateChanged", {
            previous: expected,
            current: next,
            timestamp: new Date()
        });
    }

    async connect() {
        this.transition(TCPStates.CLOSED, TCPStates.SYN_SENT);

        this.emit("packet", {
            flag: "SYN",
            sequence: this.sequenceNumber
        });

        await Promise.resolve();

        this.transition(
            TCPStates.SYN_SENT,
            TCPStates.SYN_RECEIVED
        );

        this.acknowledgmentNumber = this.sequenceNumber + 1;

        this.emit("packet", {
            flag: "SYN-ACK",
            acknowledgment: this.acknowledgmentNumber
        });

        await Promise.resolve();

        this.transition(
            TCPStates.SYN_RECEIVED,
            TCPStates.ESTABLISHED
        );

        this.emit("packet", { flag: "ACK" });

        return this.state;
    }

    async close() {
        this.transition(
            TCPStates.ESTABLISHED,
            TCPStates.FIN_WAIT
        );

        this.emit("packet", { flag: "FIN" });

        await Promise.resolve();

        this.transition(TCPStates.FIN_WAIT, TCPStates.TIME_WAIT);

        await Promise.resolve();

        this.transition(TCPStates.TIME_WAIT, TCPStates.CLOSED);

        return this.state;
    }

    createSegment(payload, flags = ["ACK"]) {
        if (this.state !== TCPStates.ESTABLISHED) {
            throw new StateTransitionError(
                "TCP connection must be established."
            );
        }

        if (!Array.isArray(flags)) {
            throw new TypeError("TCP flags must be an array.");
        }

        const allowed = new Set([
            "SYN", "ACK", "FIN", "RST", "PSH", "URG"
        ]);

        if (flags.some(flag => !allowed.has(flag))) {
            throw new ProtocolError("Invalid TCP flag.");
        }

        return {
            sourcePort: this.sourcePort,
            destinationPort: this.destinationPort,
            sequenceNumber: this.sequenceNumber,
            acknowledgmentNumber: this.acknowledgmentNumber,
            flags: [...new Set(flags)],
            payload: Buffer.from(payload)
        };
    }
}

// ============================================================
// 6. TRANSPORT LAYER: UDP
// ============================================================

class UDPDatagram {
    constructor(sourcePort, destinationPort, payload) {
        this.sourcePort = validatePort(sourcePort);
        this.destinationPort = validatePort(destinationPort);

        this.payload = Buffer.from(payload);

        if (this.payload.length > 65507) {
            throw new RangeError("UDP payload is too large.");
        }

        this.length = 8 + this.payload.length;
    }
}

// ============================================================
// 7. INTERNET LAYER
// ============================================================

class IPv4Packet {
    constructor({
        source,
        destination,
        protocol,
        payload,
        ttl = 64,
        identification = 1
    }) {
        this.source = validateIPv4(source);
        this.destination = validateIPv4(destination);

        if (!Number.isInteger(protocol) || protocol < 0 || protocol > 255) {
            throw new RangeError("Invalid IP protocol number.");
        }

        if (!Number.isInteger(ttl) || ttl < 1 || ttl > 255) {
            throw new RangeError("Invalid TTL.");
        }

        this.protocol = protocol;
        this.payload = Buffer.from(payload);
        this.ttl = ttl;
        this.identification = identification;

        this.headerLength = 20;
        this.totalLength = this.headerLength + this.payload.length;

        if (this.totalLength > 65535) {
            throw new RangeError("IPv4 packet exceeds maximum size.");
        }
    }

    forward() {
        if (this.ttl <= 1) {
            throw new RoutingError("TTL expired.");
        }

        return new IPv4Packet({
            source: this.source,
            destination: this.destination,
            protocol: this.protocol,
            payload: this.payload,
            ttl: this.ttl - 1,
            identification: this.identification
        });
    }

    inspect() {
        return {
            source: this.source,
            destination: this.destination,
            protocol: this.protocol,
            ttl: this.ttl,
            totalLength: this.totalLength
        };
    }
}

// ============================================================
// 8. NETWORK ACCESS LAYER
// ============================================================

class EthernetFrame {
    constructor(sourceMAC, destinationMAC, payload) {
        const pattern = /^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$/;

        if (!pattern.test(sourceMAC) || !pattern.test(destinationMAC)) {
            throw new TypeError("Invalid MAC address.");
        }

        this.sourceMAC = sourceMAC.toLowerCase();
        this.destinationMAC = destinationMAC.toLowerCase();
        this.payload = Buffer.from(payload);
        this.etherType = 0x0800;

        if (this.payload.length > 1500) {
            throw new RangeError("Ethernet MTU exceeded.");
        }
    }

    inspect() {
        return {
            sourceMAC: this.sourceMAC,
            destinationMAC: this.destinationMAC,
            etherType: `0x${this.etherType.toString(16)}`,
            payloadLength: this.payload.length
        };
    }
}

// ============================================================
// 9. ROUTING ENGINE
// ============================================================

class RoutingTable {
    #routes = [];

    addRoute(cidr, nextHop, interfaceName, metric = 1) {
        const network = new IPv4Network(cidr);

        validateIPv4(nextHop);

        if (!Number.isInteger(metric) || metric < 0) {
            throw new RangeError("Invalid route metric.");
        }

        this.#routes.push({
            network,
            nextHop,
            interfaceName,
            metric
        });

        this.#routes.sort(
            (a, b) =>
                b.network.prefix - a.network.prefix ||
                a.metric - b.metric
        );
    }

    lookup(destination) {
        validateIPv4(destination);

        const route = this.#routes.find(
            entry => entry.network.contains(destination)
        );

        if (!route) {
            throw new RoutingError(
                `No route to ${destination}`
            );
        }

        return route;
    }

    forward(packet) {
        const route = this.lookup(packet.destination);

        return {
            packet: packet.forward(),
            route
        };
    }

    get routes() {
        return this.#routes.map(route => ({
            network: route.network.cidr,
            nextHop: route.nextHop,
            interfaceName: route.interfaceName,
            metric: route.metric
        }));
    }
}

// ============================================================
// 10. DNS RESOLUTION WITH TTL CACHING
// ============================================================

class DNSResolver {
    #records = new Map();

    addRecord(domain, address, ttlSeconds = 60) {
        if (typeof domain !== "string" || domain.length === 0) {
            throw new TypeError("Domain is required.");
        }

        validateIPv4(address);

        if (!Number.isFinite(ttlSeconds) || ttlSeconds <= 0) {
            throw new RangeError("Invalid DNS TTL.");
        }

        this.#records.set(domain.toLowerCase(), {
            address,
            expiresAt: Date.now() + ttlSeconds * 1000
        });
    }

    async resolve(domain) {
        const key = domain.toLowerCase();
        const record = this.#records.get(key);

        if (!record) {
            throw new NetworkError("DNS record not found.");
        }

        if (Date.now() >= record.expiresAt) {
            this.#records.delete(key);

            throw new NetworkError("DNS cache entry expired.");
        }

        await Promise.resolve();

        return record.address;
    }
}

// ============================================================
// 11. NETWORK EVENT MONITOR
// ============================================================

class NetworkMonitor extends EventEmitter {
    constructor() {
        super();

        this.metrics = {
            transmitted: 0,
            received: 0,
            dropped: 0,
            errors: 0
        };
    }

    recordTransmission(packet) {
        this.metrics.transmitted++;

        this.emit("transmission", packet.inspect());
    }

    recordReception(packet) {
        this.metrics.received++;

        this.emit("reception", packet.inspect());
    }

    recordDrop(reason) {
        this.metrics.dropped++;

        this.emit("drop", { reason });
    }

    recordError(error) {
        this.metrics.errors++;

        this.emit("errorRecorded", {
            message: error.message
        });
    }

    report() {
        return { ...this.metrics };
    }
}

// ============================================================
// 12. NETWORK STACK
// ============================================================

class NetworkStack {
    constructor() {
        this.monitor = new NetworkMonitor();
    }

    encapsulate(message, source, destination, sourcePort, destinationPort) {
        const tcp = {
            sourcePort: validatePort(sourcePort),
            destinationPort: validatePort(destinationPort),
            payload: message.payload,
            flags: ["ACK", "PSH"]
        };

        const packet = new IPv4Packet({
            source,
            destination,
            protocol: 6,
            payload: tcp.payload
        });

        const frame = new EthernetFrame(
            "02:00:00:00:00:01",
            "02:00:00:00:00:02",
            packet.payload
        );

        return { message, tcp, packet, frame };
    }

    decapsulate(frame) {
        if (!(frame instanceof EthernetFrame)) {
            throw new ProtocolError("Expected Ethernet frame.");
        }

        return {
            internetPayload: frame.payload,
            etherType: frame.etherType
        };
    }

    async transmit(packet, router) {
        try {
            this.monitor.recordTransmission(packet);

            const result = router.forward(packet);

            this.monitor.recordReception(result.packet);

            return result;
        } catch (error) {
            this.monitor.recordDrop(error.message);
            this.monitor.recordError(error);

            throw error;
        }
    }
}

// ============================================================
// 13. MTU AND FRAGMENTATION
// ============================================================

function fragmentIPv4Payload(packetSize, mtu) {
    const headerSize = 20;

    if (
        !Number.isInteger(packetSize) ||
        packetSize <= headerSize ||
        packetSize > 65535
    ) {
        throw new RangeError("Invalid packet size.");
    }

    if (!Number.isInteger(mtu) || mtu <= headerSize) {
        throw new RangeError("Invalid MTU.");
    }

    const payloadSize = packetSize - headerSize;
    const maxFragmentPayload =
        Math.floor((mtu - headerSize) / 8) * 8;

    const fragments = [];

    for (let remaining = payloadSize; remaining > 0;) {
        const size = Math.min(remaining, maxFragmentPayload);

        fragments.push(size);
        remaining -= size;
    }

    return fragments;
}

// ============================================================
// 14. INTEGRATED EXECUTION
// ============================================================

async function main() {
    displayArchitecture();

    console.log("\nPROTOCOL REGISTRY");

    for (const [name, definition] of ProtocolRegistry) {
        console.log(name, definition);
    }

    console.log("\nIP NETWORK");

    const network = new IPv4Network("192.168.1.0/24");

    console.log("Network:", network.cidr);
    console.log("Broadcast:", network.broadcast);
    console.log("Contains host:", network.contains("192.168.1.25"));

    console.log("\nAPPLICATION MESSAGE");

    const message = new ApplicationMessage(
        "HTTPS",
        "GET /api/status HTTP/1.1"
    );

    const stack = new NetworkStack();

    const encapsulated = stack.encapsulate(
        message,
        "192.168.1.10",
        "203.0.113.20",
        50000,
        443
    );

    console.log("Application:", message.protocol);
    console.log("TCP:", encapsulated.tcp);
    console.log("IPv4:", encapsulated.packet.inspect());
    console.log("Ethernet:", encapsulated.frame.inspect());

    console.log("\nTCP CONNECTION");

    const connection = new TCPConnection(50000, 443);

    connection.on("stateChanged", event => {
        console.log(
            `${event.previous} -> ${event.current}`
        );
    });

    connection.on("packet", packet => {
        console.log("TCP control packet:", packet);
    });

    await connection.connect();

    console.log("Connection established:", connection.state);

    console.log("\nROUTING");

    const routingTable = new RoutingTable();

    routingTable.addRoute(
        "203.0.113.0/24",
        "192.168.1.1",
        "eth0"
    );

    routingTable.addRoute(
        "0.0.0.0/0",
        "192.168.1.254",
        "eth1",
        10
    );

    const routed = await stack.transmit(
        encapsulated.packet,
        routingTable
    );

    console.log("Selected route:", routed.route);
    console.log("Forwarded TTL:", routed.packet.ttl);

    console.log("\nDNS");

    const dns = new DNSResolver();

    dns.addRecord("example.com", "93.184.216.34", 120);

    console.log("Resolved:", await dns.resolve("example.com"));

    console.log("\nUDP");

    const datagram = new UDPDatagram(
        53000,
        53,
        Buffer.from("DNS query")
    );

    console.log("UDP length:", datagram.length);

    console.log("\nFRAGMENTATION");

    console.log(
        fragmentIPv4Payload(4000, 1500)
    );

    console.log("\nNETWORK MONITOR");

    console.log(stack.monitor.report());

    console.log("\nTCP CONNECTION TERMINATION");

    await connection.close();

    console.log("Final state:", connection.state);

    console.log("\nSIMULATION COMPLETED");
}

main().catch(error => {
    console.error("Network simulation failed:", error.message);
    process.exitCode = 1;
});
