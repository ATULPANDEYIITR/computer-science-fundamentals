"use strict";

/*
 * OSI Model: Event-Driven Network Communication Simulator.
 *
 * Demonstrates:
 * - Seven-layer processing.
 * - Event-driven packet movement.
 * - Protocol selection.
 * - Ethernet, IPv4, TCP and UDP metadata.
 * - Session lifecycle.
 * - Presentation encoding.
 * - Layer-specific fault injection.
 * - Network path diagnostics.
 * - Encapsulation and decapsulation.
 */

const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");
const net = require("node:net");

const OSI = Object.freeze({
    PHYSICAL: 1,
    DATA_LINK: 2,
    NETWORK: 3,
    TRANSPORT: 4,
    SESSION: 5,
    PRESENTATION: 6,
    APPLICATION: 7
});

const LAYER_NAMES = Object.freeze({
    1: "Physical",
    2: "Data Link",
    3: "Network",
    4: "Transport",
    5: "Session",
    6: "Presentation",
    7: "Application"
});

class NetworkError extends Error {
    constructor(layer, message) {
        super(message);
        this.name = "NetworkError";
        this.layer = layer;
    }
}

class NetworkSession {
    constructor(id, source, destination) {
        this.id = id;
        this.source = source;
        this.destination = destination;
        this.state = "ACTIVE";
        this.createdAt = Date.now();
    }

    terminate() {
        if (this.state !== "ACTIVE") {
            throw new Error("Session is not active");
        }

        this.state = "TERMINATED";
    }
}

class ProtocolRegistry {
    constructor() {
        this.protocols = new Map([
            ["HTTP", { port: 80, layer: 7 }],
            ["HTTPS", { port: 443, layer: 7 }],
            ["DNS", { port: 53, layer: 7 }],
            ["FTP", { port: 21, layer: 7 }],
            ["SSH", { port: 22, layer: 7 }],
            ["SMTP", { port: 25, layer: 7 }]
        ]);
    }

    get(name) {
        const protocol = this.protocols.get(name.toUpperCase());

        if (!protocol) {
            throw new NetworkError(
                OSI.APPLICATION,
                `Unknown application protocol: ${name}`
            );
        }

        return protocol;
    }

    register(name, port) {
        const key = name.toUpperCase();

        if (!/^[A-Z][A-Z0-9-]{1,31}$/.test(key)) {
            throw new Error("Invalid protocol name");
        }

        if (!Number.isInteger(port) || port < 1 || port > 65535) {
            throw new Error("Invalid protocol port");
        }

        if (this.protocols.has(key)) {
            throw new Error("Protocol already registered");
        }

        this.protocols.set(key, {
            port,
            layer: OSI.APPLICATION
        });
    }
}

class LayerProcessor {
    constructor(number, protocol, operation) {
        this.number = number;
        this.name = LAYER_NAMES[number];
        this.protocol = protocol;
        this.operation = operation;
    }

    execute(packet) {
        const result = this.operation(packet);

        if (result === null || result === undefined) {
            throw new NetworkError(
                this.number,
                `${this.name} returned an invalid result`
            );
        }

        return result;
    }
}

class NetworkSimulator extends EventEmitter {
    constructor() {
        super();

        this.sessions = new Map();
        this.registry = new ProtocolRegistry();
        this.statistics = new Map();

        for (let layer = 1; layer <= 7; layer++) {
            this.statistics.set(layer, {
                processed: 0,
                failures: 0
            });
        }

        this.processors = new Map([
            [1, new LayerProcessor(1, "Ethernet signaling",
                packet => Buffer.from(packet))],

            [2, new LayerProcessor(2, "Ethernet",
                packet => ({
                    destinationMAC: packet.destinationMAC,
                    sourceMAC: packet.sourceMAC,
                    payload: packet.payload
                }))],

            [3, new LayerProcessor(3, "IPv4",
                packet => ({
                    sourceIP: packet.sourceIP,
                    destinationIP: packet.destinationIP,
                    ttl: 64,
                    payload: packet.payload
                }))],

            [4, new LayerProcessor(4, "TCP/UDP",
                packet => ({
                    protocol: packet.transport,
                    sourcePort: packet.sourcePort,
                    destinationPort: packet.destinationPort,
                    payload: packet.payload
                }))],

            [5, new LayerProcessor(5, "Session",
                packet => ({
                    sessionId: packet.sessionId,
                    payload: packet.payload
                }))],

            [6, new LayerProcessor(6, "Presentation",
                packet => ({
                    encoding: "utf8",
                    payload: packet.payload
                }))],

            [7, new LayerProcessor(7, "HTTP",
                packet => ({
                    message: packet.payload.toString("utf8")
                }))]
        ]);
    }

    validateAddress(address, type) {
        if (type === "ip" && net.isIP(address) === 0) {
            throw new NetworkError(
                OSI.NETWORK,
                `Invalid IP address: ${address}`
            );
        }

        if (
            type === "mac" &&
            !/^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$/.test(address)
        ) {
            throw new NetworkError(
                OSI.DATA_LINK,
                `Invalid MAC address: ${address}`
            );
        }
    }

    createSession(source, destination) {
        const id = crypto.randomUUID();

        const session = new NetworkSession(
            id,
            source,
            destination
        );

        this.sessions.set(id, session);

        this.emit("session:opened", {
            id,
            source,
            destination
        });

        return session;
    }

    processLayer(number, packet, faultLayer = null) {
        const processor = this.processors.get(number);

        try {
            if (number === faultLayer) {
                throw new NetworkError(
                    number,
                    "Injected network-layer failure"
                );
            }

            const result = processor.execute(packet);

            const statistics = this.statistics.get(number);
            statistics.processed++;

            this.emit("layer:processed", {
                layer: number,
                name: processor.name
            });

            return result;
        } catch (error) {
            this.statistics.get(number).failures++;

            this.emit("layer:error", {
                layer: number,
                name: processor.name,
                message: error.message
            });

            throw error;
        }
    }

    async send(options) {
        const {
            sourceIP,
            destinationIP,
            sourceMAC,
            destinationMAC,
            protocol = "TCP",
            application = "HTTPS",
            message,
            faultLayer = null
        } = options;

        this.validateAddress(sourceIP, "ip");
        this.validateAddress(destinationIP, "ip");
        this.validateAddress(sourceMAC, "mac");
        this.validateAddress(destinationMAC, "mac");

        if (!["TCP", "UDP"].includes(protocol)) {
            throw new NetworkError(
                OSI.TRANSPORT,
                "Unsupported transport protocol"
            );
        }

        if (typeof message !== "string" || message.length === 0) {
            throw new NetworkError(
                OSI.APPLICATION,
                "Application message cannot be empty"
            );
        }

        const appProtocol = this.registry.get(application);

        const session = this.createSession(
            sourceIP,
            destinationIP
        );

        const packet = {
            sourceIP,
            destinationIP,
            sourceMAC,
            destinationMAC,
            sourcePort: 52000,
            destinationPort: appProtocol.port,
            transport: protocol,
            sessionId: session.id,
            payload: Buffer.from(message, "utf8")
        };

        try {
            // Encapsulation moves from application to physical layer.
            for (let layer = 7; layer >= 1; layer--) {
                await Promise.resolve();

                this.processLayer(
                    layer,
                    packet,
                    faultLayer
                );
            }

            const digest = crypto
                .createHash("sha256")
                .update(packet.payload)
                .digest("hex");

            this.emit("packet:transmitted", {
                sessionId: session.id,
                digest,
                application,
                transport: protocol
            });

            return {
                sessionId: session.id,
                payload: packet.payload,
                digest,
                state: "TRANSMITTED"
            };
        } catch (error) {
            session.terminate();

            this.emit("packet:failed", {
                sessionId: session.id,
                layer: error.layer,
                error: error.message
            });

            throw error;
        }
    }

    receive(packet) {
        if (!packet || !Buffer.isBuffer(packet.payload)) {
            throw new NetworkError(
                OSI.PHYSICAL,
                "Invalid received packet"
            );
        }

        const session = this.sessions.get(packet.sessionId);

        if (!session || session.state !== "ACTIVE") {
            throw new NetworkError(
                OSI.SESSION,
                "Communication session is unavailable"
            );
        }

        const decoded = packet.payload.toString("utf8");

        this.emit("packet:received", {
            sessionId: session.id,
            messageLength: Buffer.byteLength(decoded)
        });

        return decoded;
    }

    closeSession(id) {
        const session = this.sessions.get(id);

        if (!session) {
            throw new Error("Unknown session");
        }

        session.terminate();

        this.emit("session:closed", { id });
    }

    diagnose() {
        return [...this.statistics.entries()].map(
            ([layer, statistics]) => ({
                layer,
                name: LAYER_NAMES[layer],
                processed: statistics.processed,
                failures: statistics.failures
            })
        );
    }
}

async function main() {
    const network = new NetworkSimulator();

    network.on("layer:processed", event => {
        console.log(
            `Layer ${event.layer}: ${event.name} processed`
        );
    });

    network.on("layer:error", event => {
        console.error(
            `Layer ${event.layer} failure: ${event.message}`
        );
    });

    network.on("packet:transmitted", event => {
        console.log(
            `Packet transmitted. Session: ${event.sessionId}`
        );
    });

    network.on("session:opened", event => {
        console.log(`Session opened: ${event.id}`);
    });

    const result = await network.send({
        sourceIP: "192.168.1.10",
        destinationIP: "192.168.1.20",
        sourceMAC: "00:11:22:33:44:55",
        destinationMAC: "AA:BB:CC:DD:EE:FF",
        protocol: "TCP",
        application: "HTTPS",
        message: "OSI Model: Seven Layers"
    });

    console.log("\nPacket digest:", result.digest);
    console.log("Payload:", result.payload.toString("utf8"));

    network.closeSession(result.sessionId);

    // Test a network-layer failure.
    try {
        await network.send({
            sourceIP: "10.0.0.1",
            destinationIP: "10.0.0.2",
            sourceMAC: "00:11:22:33:44:55",
            destinationMAC: "AA:BB:CC:DD:EE:FF",
            protocol: "UDP",
            application: "DNS",
            message: "example.internal",
            faultLayer: OSI.NETWORK
        });
    } catch (error) {
        console.log("\nExpected failure:", error.message);
    }

    console.log("\nLayer diagnostics:");

    console.table(network.diagnose());

    // Verify address validation.
    try {
        network.validateAddress("300.1.1.1", "ip");
    } catch (error) {
        console.log("Validation test passed:", error.message);
    }
}

main().catch(error => {
    console.error("Network simulation failed:", error);
    process.exitCode = 1;
});
