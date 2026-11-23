"use strict";

/**
 * Physical and Data Link Layer
 * Event-driven Ethernet switch simulation.
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 *
 * Demonstrates:
 * - Binary signals
 * - NRZ and Manchester encoding
 * - MAC address validation
 * - Ethernet frame serialization
 * - CRC-32/FCS verification
 * - Event-driven frame reception
 * - MAC address learning
 * - Ethernet switching and flooding
 * - MAC table aging
 */

const { EventEmitter } = require("node:events");
const assert = require("node:assert/strict");

// ============================================================
// 1. ERRORS
// ============================================================

class NetworkError extends Error {}

class FrameIntegrityError extends NetworkError {}

class PortError extends NetworkError {}

// ============================================================
// 2. MAC ADDRESS
// ============================================================

class MACAddress {
    constructor(value) {
        if (typeof value !== "string") {
            throw new TypeError("MAC address must be a string.");
        }

        const normalized = value.replace(/-/g, ":").toUpperCase();

        if (!/^([0-9A-F]{2}:){5}[0-9A-F]{2}$/.test(normalized)) {
            throw new TypeError("Invalid MAC address.");
        }

        this.value = normalized;
        Object.freeze(this);
    }

    get bytes() {
        return Buffer.from(this.value.split(":").map(
            part => parseInt(part, 16)
        ));
    }

    get isMulticast() {
        return (this.bytes[0] & 1) !== 0;
    }

    get isBroadcast() {
        return this.value === "FF:FF:FF:FF:FF:FF";
    }

    toString() {
        return this.value;
    }

    equals(other) {
        return other instanceof MACAddress &&
            this.value === other.value;
    }
}

const BROADCAST = new MACAddress("FF:FF:FF:FF:FF:FF");

// ============================================================
// 3. SIGNAL ENCODING
// ============================================================

class SignalEncoder {
    static validate(bits) {
        if (typeof bits !== "string" || !/^[01]+$/.test(bits)) {
            throw new TypeError("Expected a non-empty binary string.");
        }
    }

    static encodeNRZ(bits) {
        this.validate(bits);
        return Array.from(bits, Number);
    }

    static decodeNRZ(signals) {
        if (!Array.isArray(signals) ||
            signals.length === 0 ||
            signals.some(value => value !== 0 && value !== 1)) {
            throw new TypeError("Invalid NRZ signals.");
        }

        return signals.join("");
    }

    static encodeManchester(bits) {
        this.validate(bits);

        return Array.from(bits, bit =>
            bit === "0" ? [0, 1] : [1, 0]
        ).flat();
    }

    static decodeManchester(signals) {
        if (!Array.isArray(signals) ||
            signals.length === 0 ||
            signals.length % 2 !== 0) {
            throw new TypeError("Invalid Manchester signal length.");
        }

        let decoded = "";

        for (let i = 0; i < signals.length; i += 2) {
            const first = signals[i];
            const second = signals[i + 1];

            if (first === 0 && second === 1) {
                decoded += "0";
            } else if (first === 1 && second === 0) {
                decoded += "1";
            } else {
                throw new FrameIntegrityError(
                    `Invalid transition at bit ${i / 2}.`
                );
            }
        }

        return decoded;
    }
}

// ============================================================
// 4. CRC-32
// ============================================================

class CRC32 {
    static table = (() => {
        const table = new Uint32Array(256);

        for (let i = 0; i < 256; i++) {
            let value = i;

            for (let bit = 0; bit < 8; bit++) {
                value = value & 1
                    ? (value >>> 1) ^ 0xEDB88320
                    : value >>> 1;
            }

            table[i] = value >>> 0;
        }

        return table;
    })();

    static calculate(buffer) {
        let crc = 0xFFFFFFFF;

        for (const byte of buffer) {
            crc = CRC32.table[(crc ^ byte) & 0xFF] ^
                (crc >>> 8);
        }

        return (crc ^ 0xFFFFFFFF) >>> 0;
    }
}

// ============================================================
// 5. ETHERNET FRAME
// ============================================================

class EthernetFrame {
    static MIN_PAYLOAD = 46;
    static MAX_PAYLOAD = 1500;

    constructor(destination, source, payload, etherType = 0x0800) {
        if (!(destination instanceof MACAddress) ||
            !(source instanceof MACAddress)) {
            throw new TypeError("Valid MAC objects are required.");
        }

        if (source.isMulticast) {
            throw new TypeError("Source MAC must be unicast.");
        }

        if (destination.equals(source)) {
            throw new TypeError("Source and destination cannot match.");
        }

        if (!Buffer.isBuffer(payload)) {
            throw new TypeError("Payload must be a Buffer.");
        }

        if (payload.length > EthernetFrame.MAX_PAYLOAD) {
            throw new RangeError("Payload exceeds Ethernet MTU.");
        }

        if (!Number.isInteger(etherType) ||
            etherType < 0 ||
            etherType > 65535) {
            throw new RangeError("Invalid EtherType.");
        }

        this.destination = destination;
        this.source = source;
        this.payload = Buffer.from(payload);
        this.etherType = etherType;

        Object.freeze(this);
    }

    serialize() {
        const header = Buffer.alloc(14);

        this.destination.bytes.copy(header, 0);
        this.source.bytes.copy(header, 6);
        header.writeUInt16BE(this.etherType, 12);

        const payload = Buffer.alloc(
            Math.max(this.payload.length, EthernetFrame.MIN_PAYLOAD)
        );

        this.payload.copy(payload);

        const content = Buffer.concat([header, payload]);

        const fcs = Buffer.alloc(4);
        fcs.writeUInt32LE(CRC32.calculate(content));

        return Buffer.concat([content, fcs]);
    }

    static deserialize(raw) {
        if (!Buffer.isBuffer(raw) ||
            raw.length < 64 ||
            raw.length > 1518) {
            throw new FrameIntegrityError("Invalid Ethernet frame length.");
        }

        const content = raw.subarray(0, -4);
        const received = raw.readUInt32LE(raw.length - 4);
        const calculated = CRC32.calculate(content);

        if (received !== calculated) {
            throw new FrameIntegrityError("FCS verification failed.");
        }

        const destination = new MACAddress(
            [...raw.subarray(0, 6)]
                .map(b => b.toString(16).padStart(2, "0"))
                .join(":")
        );

        const source = new MACAddress(
            [...raw.subarray(6, 12)]
                .map(b => b.toString(16).padStart(2, "0"))
                .join(":")
        );

        const etherType = raw.readUInt16BE(12);

        return new EthernetFrame(
            destination,
            source,
            raw.subarray(14, -4),
            etherType
        );
    }
}

// ============================================================
// 6. EVENT-DRIVEN ETHERNET SWITCH
// ============================================================

class EthernetSwitch extends EventEmitter {
    constructor(name, agingTimeMs = 300000) {
        super();

        if (!Number.isInteger(agingTimeMs) || agingTimeMs <= 0) {
            throw new RangeError("Invalid MAC aging time.");
        }

        this.name = name;
        this.agingTimeMs = agingTimeMs;
        this.ports = new Map();
        this.macTable = new Map();
        this.statistics = {
            received: 0,
            forwarded: 0,
            flooded: 0,
            dropped: 0
        };
    }

    addPort(name, mac) {
        if (this.ports.has(name)) {
            throw new PortError(`Port ${name} already exists.`);
        }

        this.ports.set(name, {
            name,
            mac,
            enabled: true
        });
    }

    setPortState(name, enabled) {
        const port = this.ports.get(name);

        if (!port) {
            throw new PortError("Unknown port.");
        }

        port.enabled = Boolean(enabled);
        this.emit("portStateChanged", {
            port: name,
            enabled: port.enabled
        });
    }

    expireMACEntries(now = Date.now()) {
        for (const [mac, entry] of this.macTable) {
            if (now - entry.lastSeen >= this.agingTimeMs) {
                this.macTable.delete(mac);

                this.emit("macExpired", {
                    mac,
                    port: entry.port
                });
            }
        }
    }

    learn(mac, port, now = Date.now()) {
        if (mac.isMulticast) {
            throw new NetworkError("Multicast sources cannot be learned.");
        }

        const previous = this.macTable.get(mac.toString());

        this.macTable.set(mac.toString(), {
            port,
            lastSeen: now
        });

        if (!previous || previous.port !== port) {
            this.emit("macLearned", {
                mac: mac.toString(),
                port,
                previousPort: previous?.port ?? null
            });
        }
    }

    receive(frame, incomingPort) {
        if (!(frame instanceof EthernetFrame)) {
            throw new TypeError("Expected an EthernetFrame.");
        }

        const ingress = this.ports.get(incomingPort);

        if (!ingress || !ingress.enabled) {
            this.statistics.dropped++;
            throw new PortError("Ingress port unavailable.");
        }

        this.statistics.received++;

        const now = Date.now();

        this.expireMACEntries(now);
        this.learn(frame.source, incomingPort, now);

        let destinations = [];

        if (frame.destination.equals(frame.source)) {
            destinations = [];
        } else if (frame.destination.isMulticast) {
            destinations = [...this.ports.values()]
                .filter(port => port.enabled &&
                    port.name !== incomingPort);
        } else {
            const entry = this.macTable.get(
                frame.destination.toString()
            );

            if (!entry) {
                destinations = [...this.ports.values()]
                    .filter(port => port.enabled &&
                        port.name !== incomingPort);

                this.statistics.flooded++;
            } else if (entry.port !== incomingPort) {
                const target = this.ports.get(entry.port);

                if (target?.enabled) {
                    destinations = [target];
                }
            }
        }

        const forwarded = destinations.map(port => port.name);

        if (forwarded.length > 0) {
            this.statistics.forwarded += forwarded.length;

            this.emit("frameForwarded", {
                frame,
                incomingPort,
                outgoingPorts: forwarded
            });
        }

        this.emit("frameProcessed", {
            destination: frame.destination.toString(),
            source: frame.source.toString(),
            incomingPort,
            outgoingPorts: forwarded
        });

        return forwarded;
    }

    getMACTable() {
        return [...this.macTable.entries()].map(([mac, entry]) => ({
            mac,
            port: entry.port,
            lastSeen: entry.lastSeen
        }));
    }
}

// ============================================================
// 7. NETWORK DEMONSTRATION
// ============================================================

async function main() {
    console.log("PHYSICAL LAYER");

    const bits = "10110010";

    const encoded = SignalEncoder.encodeManchester(bits);

    console.log("Original bits:", bits);
    console.log("Manchester:", encoded);
    console.log(
        "Decoded:",
        SignalEncoder.decodeManchester(encoded)
    );

    assert.equal(
        SignalEncoder.decodeManchester(encoded),
        bits
    );

    console.log("\nDATA LINK LAYER");

    const macA = new MACAddress("00:11:22:33:44:AA");
    const macB = new MACAddress("00:11:22:33:44:BB");
    const macC = new MACAddress("00:11:22:33:44:CC");

    const ethernetSwitch = new EthernetSwitch("SW-01");

    ethernetSwitch.addPort("port1", macA);
    ethernetSwitch.addPort("port2", macB);
    ethernetSwitch.addPort("port3", macC);

    ethernetSwitch.on("macLearned", event => {
        console.log("MAC learned:", event);
    });

    ethernetSwitch.on("frameForwarded", event => {
        console.log("Frame forwarded:", event.outgoingPorts);
    });

    ethernetSwitch.on("macExpired", event => {
        console.log("MAC expired:", event);
    });

    const frame = new EthernetFrame(
        macB,
        macA,
        Buffer.from("Ethernet data")
    );

    const serialized = frame.serialize();

    console.log("Frame length:", serialized.length);
    console.log(
        "CRC-32:",
        CRC32.calculate(serialized.subarray(0, -4)).toString(16)
    );

    const decoded = EthernetFrame.deserialize(serialized);

    assert.equal(decoded.source.toString(), macA.toString());

    console.log("\nUnknown destination flooding:");
    console.log(ethernetSwitch.receive(decoded, "port1"));

    const response = new EthernetFrame(
        macA,
        macB,
        Buffer.from("Acknowledgement")
    );

    console.log("\nLearned destination forwarding:");
    console.log(ethernetSwitch.receive(response, "port2"));

    console.log("\nBroadcast:");
    const broadcast = new EthernetFrame(
        BROADCAST,
        macA,
        Buffer.from("Discovery")
    );

    console.log(ethernetSwitch.receive(broadcast, "port1"));

    console.log("\nMAC table:");
    console.table(ethernetSwitch.getMACTable());

    console.log("\nStatistics:");
    console.table(ethernetSwitch.statistics);

    // A corrupted frame must be rejected.
    const corrupted = Buffer.from(serialized);
    corrupted[20] ^= 0x01;

    assert.throws(
        () => EthernetFrame.deserialize(corrupted),
        FrameIntegrityError
    );

    // An invalid Manchester signal must also be rejected.
    assert.throws(
        () => SignalEncoder.decodeManchester([0, 0]),
        FrameIntegrityError
    );

    console.log("\nAll validation checks passed.");
}

main().catch(error => {
    console.error("Network simulation failed:", error.message);
    process.exitCode = 1;
});
