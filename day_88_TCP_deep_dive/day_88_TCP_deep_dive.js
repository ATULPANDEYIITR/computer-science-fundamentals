"use strict";

/*
 * TCP Deep Dive: Event-driven transport protocol simulator.
 *
 * Covers:
 * - Three-way connection establishment
 * - TCP sequence and acknowledgment numbers
 * - Sliding-window transmission
 * - Cumulative ACK processing
 * - Duplicate ACK detection
 * - Retransmission timers
 * - RTT estimation
 * - Congestion control
 * - Receiver flow control
 * - Connection termination
 *
 * Runtime: Node.js 18+
 *
 * Run: node tcp_deep_dive.js
 */

const { EventEmitter } = require("node:events");
const { randomUUID } = require("node:crypto");

const TCPState = Object.freeze({
    CLOSED: "CLOSED",
    LISTEN: "LISTEN",
    SYN_SENT: "SYN_SENT",
    SYN_RECEIVED: "SYN_RECEIVED",
    ESTABLISHED: "ESTABLISHED",
    FIN_WAIT_1: "FIN_WAIT_1",
    FIN_WAIT_2: "FIN_WAIT_2",
    CLOSE_WAIT: "CLOSE_WAIT",
    LAST_ACK: "LAST_ACK",
    TIME_WAIT: "TIME_WAIT"
});

const CongestionState = Object.freeze({
    SLOW_START: "SLOW_START",
    CONGESTION_AVOIDANCE: "CONGESTION_AVOIDANCE",
    FAST_RECOVERY: "FAST_RECOVERY"
});

class TCPError extends Error {
    constructor(message, code = "TCP_ERROR") {
        super(message);
        this.name = "TCPError";
        this.code = code;
    }
}

class NetworkLink extends EventEmitter {
    constructor({ lossRate = 0, latencyMs = 10, seed = 123 } = {}) {
        super();

        if (lossRate < 0 || lossRate > 1) {
            throw new RangeError("lossRate must be between 0 and 1");
        }

        if (latencyMs < 0) {
            throw new RangeError("Latency cannot be negative");
        }

        this.lossRate = lossRate;
        this.latencyMs = latencyMs;
        this.seed = seed;
        this.sequence = 0;
    }

    random() {
        // Deterministic pseudo-random generator for repeatable tests.
        this.seed = (this.seed * 16807) % 2147483647;
        return (this.seed - 1) / 2147483646;
    }

    transmit(segment) {
        return new Promise((resolve, reject) => {
            const packet = {
                ...segment,
                packetId: randomUUID()
            };

            if (this.random() < this.lossRate) {
                this.emit("drop", packet);
                reject(new TCPError(
                    `Packet ${packet.packetId} was dropped`,
                    "PACKET_LOSS"
                ));
                return;
            }

            setTimeout(() => {
                this.emit("delivery", packet);
                resolve(packet);
            }, this.latencyMs);
        });
    }
}

class RTTEstimator {
    constructor() {
        this.srtt = null;
        this.rttvar = null;
        this.rto = 1000;
        this.minimumRto = 200;
        this.maximumRto = 60000;
    }

    observe(sampleMs) {
        if (!Number.isFinite(sampleMs) || sampleMs <= 0) {
            throw new RangeError("RTT sample must be positive");
        }

        if (this.srtt === null) {
            this.srtt = sampleMs;
            this.rttvar = sampleMs / 2;
        } else {
            const variation = Math.abs(this.srtt - sampleMs);

            this.rttvar =
                0.75 * this.rttvar +
                0.25 * variation;

            this.srtt =
                0.875 * this.srtt +
                0.125 * sampleMs;
        }

        this.rto = Math.min(
            this.maximumRto,
            Math.max(
                this.minimumRto,
                this.srtt + 4 * this.rttvar
            )
        );

        return this.rto;
    }

    backoff() {
        this.rto = Math.min(
            this.rto * 2,
            this.maximumRto
        );

        return this.rto;
    }
}

class CongestionController extends EventEmitter {
    constructor({ mss = 1000, initialWindow = 1, threshold = 16 } = {}) {
        super();

        if (mss <= 0 || initialWindow <= 0 || threshold <= 0) {
            throw new RangeError("Invalid congestion-control parameters");
        }

        this.mss = mss;
        this.cwnd = initialWindow;
        this.ssthresh = threshold;
        this.state = CongestionState.SLOW_START;
    }

    acknowledge() {
        if (this.state === CongestionState.SLOW_START) {
            this.cwnd += 1;

            if (this.cwnd >= this.ssthresh) {
                this.state = CongestionState.CONGESTION_AVOIDANCE;
            }
        } else if (
            this.state === CongestionState.CONGESTION_AVOIDANCE
        ) {
            this.cwnd += 1 / this.cwnd;
        } else {
            this.cwnd = this.ssthresh;
            this.state = CongestionState.CONGESTION_AVOIDANCE;
        }

        this.emit("window", this.snapshot());
    }

    duplicateAcknowledgment() {
        this.emit("duplicateAck");

        this.ssthresh = Math.max(this.cwnd / 2, 2);
        this.cwnd = this.ssthresh + 3;
        this.state = CongestionState.FAST_RECOVERY;

        this.emit("window", this.snapshot());
    }

    timeout() {
        this.ssthresh = Math.max(this.cwnd / 2, 2);
        this.cwnd = 1;
        this.state = CongestionState.SLOW_START;

        this.emit("timeout", this.snapshot());
        this.emit("window", this.snapshot());
    }

    snapshot() {
        return Object.freeze({
            cwnd: this.cwnd,
            ssthresh: this.ssthresh,
            state: this.state
        });
    }
}

class TCPSender extends EventEmitter {
    constructor({
        initialSequence = 1000,
        mss = 1000,
        receiverWindow = 64000
    } = {}) {
        super();

        if (
            !Number.isSafeInteger(initialSequence) ||
            initialSequence < 0
        ) {
            throw new RangeError("Invalid initial sequence number");
        }

        if (!Number.isInteger(mss) || mss <= 0) {
            throw new RangeError("Invalid MSS");
        }

        this.state = TCPState.CLOSED;

        this.iss = initialSequence;
        this.sndUna = initialSequence;
        this.sndNxt = initialSequence;
        this.rcvNxt = 0;

        this.mss = mss;
        this.rwnd = receiverWindow;

        this.congestion = new CongestionController({ mss });
        this.rtt = new RTTEstimator();

        this.outstanding = new Map();
        this.duplicateAcks = 0;

        this.stats = {
            transmitted: 0,
            retransmitted: 0,
            acknowledgedBytes: 0,
            dropped: 0
        };
    }

    connect(peer) {
        if (this.state !== TCPState.CLOSED) {
            throw new TCPError("Sender is not closed");
        }

        if (
            peer.state !== TCPState.CLOSED &&
            peer.state !== TCPState.LISTEN
        ) {
            throw new TCPError("Peer cannot accept a connection");
        }

        this.state = TCPState.SYN_SENT;
        peer.state = TCPState.LISTEN;

        const syn = {
            sequence: this.sndNxt,
            flags: ["SYN"]
        };

        this.sndNxt++;

        peer.rcvNxt = syn.sequence + 1;
        peer.iss = peer.sndNxt;
        peer.sndUna = peer.iss;
        peer.sndNxt++;

        peer.state = TCPState.SYN_RECEIVED;

        const synAck = {
            sequence: peer.iss,
            acknowledgment: peer.rcvNxt,
            flags: ["SYN", "ACK"]
        };

        this.rcvNxt = synAck.sequence + 1;
        this.sndUna = synAck.acknowledgment;

        const ack = {
            sequence: this.sndNxt,
            acknowledgment: this.rcvNxt,
            flags: ["ACK"]
        };

        peer.sndUna = ack.acknowledgment;

        this.state = TCPState.ESTABLISHED;
        peer.state = TCPState.ESTABLISHED;

        this.emit("connected", { syn, synAck, ack });

        return { syn, synAck, ack };
    }

    async send(payload, link, receiver) {
        if (this.state !== TCPState.ESTABLISHED) {
            throw new TCPError("Connection is not established");
        }

        if (!Buffer.isBuffer(payload)) {
            throw new TypeError("Payload must be a Buffer");
        }

        const congestionLimit =
            Math.floor(this.congestion.cwnd * this.mss);

        const limit = Math.min(congestionLimit, this.rwnd);

        const inFlight = this.sndNxt - this.sndUna;
        const available = Math.max(0, limit - inFlight);

        const chunk = payload.subarray(
            0,
            Math.min(this.mss, available)
        );

        if (chunk.length === 0) {
            return 0;
        }

        const sequence = this.sndNxt;

        const segment = {
            sequence,
            acknowledgment: receiver.rcvNxt,
            flags: ["ACK"],
            payload: Buffer.from(chunk),
            sentAt: Date.now()
        };

        this.outstanding.set(sequence, {
            segment,
            sentAt: Date.now(),
            retransmitted: false
        });

        this.sndNxt += chunk.length;
        this.stats.transmitted++;

        try {
            await link.transmit(segment);
            receiver.receive(segment, this);
        } catch (error) {
            if (error.code !== "PACKET_LOSS") {
                throw error;
            }

            this.stats.dropped++;
            this.emit("packetLost", segment);
        }

        return chunk.length;
    }

    receiveAcknowledgment(acknowledgment) {
        if (
            !Number.isSafeInteger(acknowledgment) ||
            acknowledgment < 0 ||
            acknowledgment > this.sndNxt
        ) {
            throw new TCPError("Invalid acknowledgment number", "BAD_ACK");
        }

        if (acknowledgment < this.sndUna) {
            return;
        }

        if (acknowledgment === this.sndUna) {
            this.duplicateAcks++;

            if (this.duplicateAcks === 3) {
                this.congestion.duplicateAcknowledgment();
                this.retransmitOldest();
            }

            return;
        }

        const bytesAcknowledged = acknowledgment - this.sndUna;

        this.sndUna = acknowledgment;
        this.duplicateAcks = 0;

        for (const [sequence, item] of this.outstanding) {
            const end = sequence + item.segment.payload.length;

            if (end <= acknowledgment) {
                // Karn's rule: do not sample RTT from retransmitted data.
                if (!item.retransmitted) {
                    this.rtt.observe(Date.now() - item.sentAt);
                }

                this.outstanding.delete(sequence);
            }
        }

        this.stats.acknowledgedBytes += bytesAcknowledged;
        this.congestion.acknowledge();

        this.emit("acknowledged", {
            acknowledgment,
            bytesAcknowledged,
            outstanding: this.outstanding.size
        });
    }

    retransmitOldest() {
        if (this.outstanding.size === 0) {
            return null;
        }

        const sequence = Math.min(...this.outstanding.keys());
        const item = this.outstanding.get(sequence);

        item.retransmitted = true;
        item.sentAt = Date.now();

        this.stats.retransmitted++;

        this.emit("retransmission", item.segment);

        return item.segment;
    }

    processTimeout(sequence) {
        const item = this.outstanding.get(sequence);

        if (!item) {
            return false;
        }

        this.rtt.backoff();
        this.congestion.timeout();

        item.retransmitted = true;
        item.sentAt = Date.now();

        this.stats.retransmitted++;

        this.emit("timeout", {
            sequence,
            rto: this.rtt.rto
        });

        return true;
    }

    snapshot() {
        return Object.freeze({
            state: this.state,
            sndUna: this.sndUna,
            sndNxt: this.sndNxt,
            cwnd: this.congestion.cwnd,
            ssthresh: this.congestion.ssthresh,
            congestionState: this.congestion.state,
            rto: this.rtt.rto,
            outstanding: this.outstanding.size,
            statistics: { ...this.stats }
        });
    }
}

class TCPReceiver extends EventEmitter {
    constructor({ initialSequence = 5000, capacity = 64000 } = {}) {
        super();

        if (capacity < 0) {
            throw new RangeError("Invalid receiver capacity");
        }

        this.state = TCPState.CLOSED;
        this.iss = initialSequence;
        this.sndUna = initialSequence;
        this.sndNxt = initialSequence;
        this.rcvNxt = 0;
        this.capacity = capacity;
        this.received = [];
    }

    receive(segment, sender) {
        if (this.state !== TCPState.ESTABLISHED) {
            throw new TCPError("Receiver is not established");
        }

        if (segment.sequence === this.rcvNxt) {
            this.received.push(Buffer.from(segment.payload));
            this.rcvNxt += segment.payload.length;

            this.emit("data", {
                bytes: segment.payload.length,
                nextExpected: this.rcvNxt
            });
        } else {
            this.emit("outOfOrder", {
                expected: this.rcvNxt,
                received: segment.sequence
            });
        }

        // Duplicate ACKs communicate the next missing byte.
        sender.receiveAcknowledgment(this.rcvNxt);
    }

    get data() {
        return Buffer.concat(this.received);
    }
}

class TCPConnectionManager extends EventEmitter {
    constructor() {
        super();
        this.connections = new Map();
    }

    add(id, sender, receiver) {
        if (this.connections.has(id)) {
            throw new TCPError("Connection identifier already exists");
        }

        this.connections.set(id, { sender, receiver });
        this.emit("connectionAdded", id);
    }

    remove(id) {
        if (!this.connections.delete(id)) {
            throw new TCPError("Unknown connection");
        }

        this.emit("connectionRemoved", id);
    }

    get(id) {
        const connection = this.connections.get(id);

        if (!connection) {
            throw new TCPError("Connection not found");
        }

        return connection;
    }
}

async function demonstrate() {
    console.log("=== TCP DEEP DIVE ===\n");

    const link = new NetworkLink({
        lossRate: 0,
        latencyMs: 5
    });

    link.on("delivery", packet => {
        console.log(`Packet delivered: ${packet.sequence}`);
    });

    link.on("drop", packet => {
        console.log(`Packet dropped: ${packet.sequence}`);
    });

    const sender = new TCPSender();
    const receiver = new TCPReceiver();

    const manager = new TCPConnectionManager();

    const connectionId = randomUUID();

    manager.add(connectionId, sender, receiver);

    sender.on("connected", handshake => {
        console.log("Three-way handshake:");
        console.log("SYN:", handshake.syn);
        console.log("SYN-ACK:", handshake.synAck);
        console.log("ACK:", handshake.ack);
    });

    sender.connect(receiver);

    console.log("\nConnection state:", sender.state);

    sender.on("acknowledged", event => {
        console.log("ACK:", event.acknowledgment);
        console.log("Acknowledged bytes:", event.bytesAcknowledged);
    });

    receiver.on("data", event => {
        console.log("Receiver accepted bytes:", event.bytes);
    });

    const message = Buffer.from(
        "Reliable transmission using TCP sliding windows."
    );

    let offset = 0;

    while (offset < message.length) {
        const sent = await sender.send(
            message.subarray(offset),
            link,
            receiver
        );

        if (sent === 0) {
            break;
        }

        offset += sent;
    }

    console.log("\nReceived message:", receiver.data.toString());

    console.log("\nConnection statistics:");
    console.log(sender.snapshot());

    console.log("\nRTT estimation:");

    for (const sample of [120, 150, 110, 180, 140]) {
        console.log(
            `${sample} ms sample -> ` +
            `${sender.rtt.observe(sample).toFixed(2)} ms RTO`
        );
    }

    console.log("\nTimeout demonstration:");

    const testSender = new TCPSender();
    testSender.state = TCPState.ESTABLISHED;

    testSender.sndNxt += 1000;

    testSender.outstanding.set(1000, {
        segment: {
            sequence: 1000,
            payload: Buffer.alloc(1000)
        },
        sentAt: Date.now(),
        retransmitted: false
    });

    testSender.on("timeout", event => {
        console.log("Timeout detected:", event);
    });

    testSender.processTimeout(1000);

    console.log("\nConnection manager:", manager.get(connectionId).sender.state);
}

demonstrate().catch(error => {
    console.error("TCP simulation failed:", error.message);
    process.exitCode = 1;
});
