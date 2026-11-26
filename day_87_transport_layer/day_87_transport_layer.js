"use strict";

/*
 * Transport Layer Engineering
 *
 * Demonstrates:
 * - TCP and UDP socket communication.
 * - Port allocation and endpoint validation.
 * - TCP connection lifecycle.
 * - Asynchronous networking with Node.js.
 * - Sliding-window flow control.
 * - Backpressure and buffer management.
 * - Timeout and socket error handling.
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library.
 */

const net = require("node:net");
const dgram = require("node:dgram");
const { EventEmitter } = require("node:events");

const HOST = "127.0.0.1";
const MAX_DATAGRAM = 1200;

class TransportError extends Error {
    constructor(message, code = "TRANSPORT_ERROR") {
        super(message);
        this.name = "TransportError";
        this.code = code;
    }
}

const Protocol = Object.freeze({
    TCP: "TCP",
    UDP: "UDP"
});

const ConnectionState = Object.freeze({
    CLOSED: "CLOSED",
    LISTEN: "LISTEN",
    SYN_SENT: "SYN_SENT",
    SYN_RECEIVED: "SYN_RECEIVED",
    ESTABLISHED: "ESTABLISHED",
    FIN_WAIT: "FIN_WAIT"
});

class Endpoint {
    constructor(address, port) {
        if (net.isIP(address) !== 4) {
            throw new TypeError("A valid IPv4 address is required.");
        }

        if (!Number.isInteger(port) || port < 0 || port > 65535) {
            throw new RangeError("Port must be between 0 and 65535.");
        }

        this.address = address;
        this.port = port;
        Object.freeze(this);
    }

    toString() {
        return `${this.address}:${this.port}`;
    }
}

class Connection extends EventEmitter {
    constructor(local, remote) {
        super();

        this.local = local;
        this.remote = remote;
        this.state = ConnectionState.CLOSED;
        this.sequence = 0;
    }

    transition(nextState) {
        const transitions = {
            CLOSED: ["SYN_SENT"],
            SYN_SENT: ["SYN_RECEIVED", "CLOSED"],
            SYN_RECEIVED: ["ESTABLISHED", "CLOSED"],
            ESTABLISHED: ["FIN_WAIT"],
            FIN_WAIT: ["CLOSED"]
        };

        if (!transitions[this.state]?.includes(nextState)) {
            throw new TransportError(
                `Invalid transition: ${this.state} -> ${nextState}`
            );
        }

        const previous = this.state;
        this.state = nextState;

        this.emit("stateChange", {
            previous,
            current: nextState
        });
    }

    establish() {
        this.transition(ConnectionState.SYN_SENT);
        this.emit("segment", "SYN");

        this.transition(ConnectionState.SYN_RECEIVED);
        this.emit("segment", "SYN-ACK");

        this.transition(ConnectionState.ESTABLISHED);
        this.emit("segment", "ACK");
    }

    close() {
        this.transition(ConnectionState.FIN_WAIT);
        this.emit("segment", "FIN");
        this.transition(ConnectionState.CLOSED);
    }
}

class SlidingWindow extends EventEmitter {
    constructor(initialWindow) {
        super();

        if (!Number.isSafeInteger(initialWindow) ||
            initialWindow <= 0) {
            throw new RangeError("Window size must be positive.");
        }

        this.windowSize = initialWindow;
        this.maximumWindow = 65535;
        this.nextSequence = 0;
        this.lastAcknowledged = 0;
        this.pending = new Map();
    }

    get inFlightBytes() {
        let total = 0;

        for (const segment of this.pending.values()) {
            total += segment.length;
        }

        return total;
    }

    get availableWindow() {
        return Math.max(0, this.windowSize - this.inFlightBytes);
    }

    send(data) {
        if (!Buffer.isBuffer(data)) {
            data = Buffer.from(data);
        }

        if (data.length === 0) {
            throw new TypeError("Cannot transmit an empty segment.");
        }

        if (data.length > this.availableWindow) {
            this.emit("blocked", {
                requested: data.length,
                available: this.availableWindow
            });

            return null;
        }

        const sequence = this.nextSequence;

        this.pending.set(sequence, {
            length: data.length,
            data: Buffer.from(data),
            sentAt: Date.now()
        });

        this.nextSequence += data.length;

        this.emit("sent", {
            sequence,
            length: data.length,
            availableWindow: this.availableWindow
        });

        return sequence;
    }

    acknowledge(ackNumber) {
        if (!Number.isSafeInteger(ackNumber) ||
            ackNumber < this.lastAcknowledged ||
            ackNumber > this.nextSequence) {
            throw new TransportError("Invalid cumulative ACK.");
        }

        if (ackNumber === this.lastAcknowledged) {
            return;
        }

        for (const [sequence, segment] of this.pending) {
            if (sequence + segment.length <= ackNumber) {
                this.pending.delete(sequence);
            }
        }

        this.lastAcknowledged = ackNumber;

        this.emit("acknowledged", {
            ackNumber,
            availableWindow: this.availableWindow
        });
    }

    advertiseWindow(size) {
        if (!Number.isSafeInteger(size) ||
            size < 0 || size > this.maximumWindow) {
            throw new RangeError("Invalid advertised window.");
        }

        this.windowSize = size;
        this.emit("windowUpdate", size);
    }

    getTimedOutSegments(timeoutMs) {
        if (timeoutMs <= 0) {
            throw new RangeError("Timeout must be positive.");
        }

        const now = Date.now();
        const expired = [];

        for (const [sequence, segment] of this.pending) {
            if (now - segment.sentAt >= timeoutMs) {
                expired.push({
                    sequence,
                    data: Buffer.from(segment.data)
                });
            }
        }

        return expired;
    }
}

function createTCPServer() {
    const server = net.createServer((socket) => {
        socket.setTimeout(5000);

        console.log(
            "TCP connection:",
            `${socket.remoteAddress}:${socket.remotePort}`
        );

        socket.on("data", (data) => {
            console.log("TCP received:", data.length, "bytes");

            if (!socket.destroyed) {
                socket.write(Buffer.concat([
                    Buffer.from("TCP-ACK:"),
                    data
                ]));
            }
        });

        socket.on("timeout", () => {
            socket.destroy(new Error("TCP idle timeout."));
        });

        socket.on("error", (error) => {
            console.error("TCP client error:", error.message);
        });
    });

    return server;
}

function startTCPServer(server) {
    return new Promise((resolve, reject) => {
        const onError = (error) => reject(error);

        server.once("error", onError);

        server.listen(0, HOST, () => {
            server.removeListener("error", onError);

            resolve(new Endpoint(
                HOST,
                server.address().port
            ));
        });
    });
}

function sendTCP(endpoint, payload) {
    return new Promise((resolve, reject) => {
        const socket = net.createConnection({
            host: endpoint.address,
            port: endpoint.port
        });

        const timeout = setTimeout(() => {
            socket.destroy(new Error("TCP client timeout."));
        }, 5000);

        const chunks = [];

        socket.once("connect", () => {
            socket.write(payload);
        });

        socket.on("data", (chunk) => {
            chunks.push(chunk);
            socket.end();
        });

        socket.once("end", () => {
            clearTimeout(timeout);
            resolve(Buffer.concat(chunks));
        });

        socket.once("error", (error) => {
            clearTimeout(timeout);
            reject(error);
        });
    });
}

function createUDPServer() {
    const server = dgram.createSocket("udp4");

    server.on("message", (message, remote) => {
        console.log(
            "UDP received:",
            message.length,
            "bytes from",
            `${remote.address}:${remote.port}`
        );

        const response = Buffer.concat([
            Buffer.from("UDP-ACK:"),
            message
        ]);

        if (response.length > MAX_DATAGRAM) {
            console.error("UDP response exceeds configured limit.");
            return;
        }

        server.send(
            response,
            remote.port,
            remote.address,
            (error) => {
                if (error) {
                    console.error("UDP send failure:", error.message);
                }
            }
        );
    });

    server.on("error", (error) => {
        console.error("UDP server error:", error.message);
    });

    return server;
}

function startUDPServer(server) {
    return new Promise((resolve, reject) => {
        server.once("error", reject);

        server.bind(0, HOST, () => {
            server.removeAllListeners("error");

            resolve(new Endpoint(
                HOST,
                server.address().port
            ));
        });
    });
}

function sendUDP(endpoint, payload) {
    return new Promise((resolve, reject) => {
        const client = dgram.createSocket("udp4");

        const timer = setTimeout(() => {
            client.close();
            reject(new Error("UDP response timeout."));
        }, 3000);

        client.once("message", (message) => {
            clearTimeout(timer);
            client.close();
            resolve(message);
        });

        client.once("error", (error) => {
            clearTimeout(timer);
            client.close();
            reject(error);
        });

        client.send(
            payload,
            endpoint.port,
            endpoint.address,
            (error) => {
                if (error) {
                    clearTimeout(timer);
                    client.close();
                    reject(error);
                }
            }
        );
    });
}

async function demonstrateTCP() {
    console.log("\n--- TCP Communication ---");

    const server = createTCPServer();

    try {
        const endpoint = await startTCPServer(server);

        console.log("TCP listening on", endpoint.toString());

        const response = await sendTCP(
            endpoint,
            Buffer.from("Hello over TCP")
        );

        console.log("TCP response:", response.toString());
    } finally {
        await new Promise((resolve) => server.close(resolve));
    }
}

async function demonstrateUDP() {
    console.log("\n--- UDP Communication ---");

    const server = createUDPServer();

    try {
        const endpoint = await startUDPServer(server);

        console.log("UDP listening on", endpoint.toString());

        const response = await sendUDP(
            endpoint,
            Buffer.from("Hello over UDP")
        );

        console.log("UDP response:", response.toString());
    } finally {
        server.close();
    }
}

function demonstrateConnection() {
    console.log("\n--- TCP Connection State ---");

    const connection = new Connection(
        new Endpoint(HOST, 50000),
        new Endpoint(HOST, 443)
    );

    connection.on("stateChange", (event) => {
        console.log(
            `${event.previous} -> ${event.current}`
        );
    });

    connection.on("segment", (segment) => {
        console.log("TCP segment:", segment);
    });

    connection.establish();
    connection.close();
}

function demonstrateFlowControl() {
    console.log("\n--- Sliding Window ---");

    const window = new SlidingWindow(10);

    window.on("sent", console.log);
    window.on("blocked", console.log);
    window.on("acknowledged", console.log);
    window.on("windowUpdate", (size) => {
        console.log("New advertised window:", size);
    });

    window.send(Buffer.from("123456"));
    window.send(Buffer.from("ABCD"));
    window.send(Buffer.from("XYZ"));

    window.acknowledge(6);

    window.send(Buffer.from("XYZ"));

    window.acknowledge(13);
    window.advertiseWindow(12);

    window.send(Buffer.from("PAYLOAD"));
}

async function main() {
    console.log("TRANSPORT LAYER ENGINEERING");

    demonstrateConnection();
    demonstrateFlowControl();

    await demonstrateTCP();
    await demonstrateUDP();

    console.log("\nDemonstration completed.");
}

main().catch((error) => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
