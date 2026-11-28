"use strict";

/*
 * Application Layer Protocols
 * HTTP, HTTPS, DNS, SMTP, FTP and SSH
 *
 * Event-driven protocol monitoring and policy evaluation.
 * Runtime: Node.js 18+
 */

const https = require("node:https");
const http = require("node:http");
const dns = require("node:dns").promises;
const net = require("node:net");
const crypto = require("node:crypto");
const { EventEmitter } = require("node:events");

// ============================================================
// 1. Protocol definitions
// ============================================================

const Protocol = Object.freeze({
    HTTP: "HTTP",
    HTTPS: "HTTPS",
    DNS: "DNS",
    SMTP: "SMTP",
    FTP: "FTP",
    SSH: "SSH"
});

const ProtocolRegistry = new Map([
    ["HTTP", { port: 80, transport: "TCP", encrypted: false }],
    ["HTTPS", { port: 443, transport: "TCP", encrypted: true }],
    ["DNS", { port: 53, transport: "UDP/TCP", encrypted: false }],
    ["SMTP", { port: 587, transport: "TCP", encrypted: true }],
    ["FTP", { port: 21, transport: "TCP", encrypted: false }],
    ["SSH", { port: 22, transport: "TCP", encrypted: true }]
]);

class ProtocolError extends Error {
    constructor(message, code = "PROTOCOL_ERROR") {
        super(message);
        this.name = "ProtocolError";
        this.code = code;
    }
}

function validateHostname(hostname) {
    if (typeof hostname !== "string" || !hostname.trim()) {
        throw new ProtocolError("Hostname is required.");
    }

    const normalized = hostname.toLowerCase().replace(/\.$/, "");

    if (normalized.length > 253) {
        throw new ProtocolError("Hostname exceeds maximum length.");
    }

    const labels = normalized.split(".");

    for (const label of labels) {
        if (
            label.length > 63 ||
            !/^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/.test(label)
        ) {
            throw new ProtocolError(`Invalid DNS label: ${label}`);
        }
    }

    return normalized;
}

// ============================================================
// 2. Event-driven protocol monitoring
// ============================================================

class ProtocolMonitor extends EventEmitter {
    constructor() {
        super();
        this.metrics = new Map();
        this.events = [];
    }

    record(event) {
        const required = ["protocol", "operation", "success"];

        for (const field of required) {
            if (!(field in event)) {
                throw new ProtocolError(
                    `Missing monitoring field: ${field}`
                );
            }
        }

        if (!ProtocolRegistry.has(event.protocol)) {
            throw new ProtocolError("Unknown protocol.");
        }

        const normalized = Object.freeze({
            ...event,
            timestamp: new Date().toISOString()
        });

        this.events.push(normalized);

        const current = this.metrics.get(event.protocol) || {
            requests: 0,
            failures: 0,
            successes: 0
        };

        current.requests++;

        if (event.success) {
            current.successes++;
        } else {
            current.failures++;
        }

        this.metrics.set(event.protocol, current);

        this.emit("protocol-event", normalized);

        if (!event.success) {
            this.emit("protocol-failure", normalized);
        }
    }

    report() {
        return Object.fromEntries(
            [...this.metrics.entries()].map(
                ([protocol, values]) => [
                    protocol,
                    { ...values }
                ]
            )
        );
    }
}

// ============================================================
// 3. Policy engine
// ============================================================

class NetworkPolicy {
    constructor({
        allowedProtocols,
        requireEncryption = true,
        allowedPorts = null
    }) {
        this.allowedProtocols = new Set(allowedProtocols);
        this.requireEncryption = requireEncryption;
        this.allowedPorts = allowedPorts
            ? new Set(allowedPorts)
            : null;
    }

    evaluate(protocol, port) {
        const definition = ProtocolRegistry.get(protocol);

        if (!definition) {
            return {
                allowed: false,
                reason: "Unknown protocol."
            };
        }

        if (!this.allowedProtocols.has(protocol)) {
            return {
                allowed: false,
                reason: "Protocol is not permitted."
            };
        }

        if (
            this.requireEncryption &&
            !definition.encrypted
        ) {
            return {
                allowed: false,
                reason: "Unencrypted protocol is prohibited."
            };
        }

        if (
            this.allowedPorts &&
            !this.allowedPorts.has(port)
        ) {
            return {
                allowed: false,
                reason: "Port is not permitted."
            };
        }

        return {
            allowed: true,
            reason: "Policy conditions satisfied."
        };
    }
}

// ============================================================
// 4. DNS resolution and caching
// ============================================================

class DNSResolver {
    constructor(ttlMilliseconds = 60000) {
        this.ttl = ttlMilliseconds;
        this.cache = new Map();
    }

    async resolve(hostname, recordType = "A") {
        hostname = validateHostname(hostname);

        if (!["A", "AAAA", "MX", "TXT", "NS", "CNAME"].includes(recordType)) {
            throw new ProtocolError("Unsupported DNS record type.");
        }

        const key = `${hostname}:${recordType}`;
        const cached = this.cache.get(key);

        if (cached && cached.expiresAt > Date.now()) {
            return {
                records: cached.records,
                cached: true
            };
        }

        const resolvers = {
            A: dns.resolve4,
            AAAA: dns.resolve6,
            MX: dns.resolveMx,
            TXT: dns.resolveTxt,
            NS: dns.resolveNs,
            CNAME: dns.resolveCname
        };

        const records = await resolvers[recordType](hostname);

        this.cache.set(key, {
            records,
            expiresAt: Date.now() + this.ttl
        });

        return {
            records,
            cached: false
        };
    }

    clearExpired() {
        const now = Date.now();

        for (const [key, value] of this.cache) {
            if (value.expiresAt <= now) {
                this.cache.delete(key);
            }
        }
    }
}

// ============================================================
// 5. HTTP and HTTPS client
// ============================================================

class WebClient {
    constructor(timeout = 5000, maxResponseBytes = 1048576) {
        this.timeout = timeout;
        this.maxResponseBytes = maxResponseBytes;
    }

    request(url, options = {}) {
        return new Promise((resolve, reject) => {
            let parsed;

            try {
                parsed = new URL(url);
            } catch {
                reject(new ProtocolError("Invalid URL."));
                return;
            }

            if (!["http:", "https:"].includes(parsed.protocol)) {
                reject(new ProtocolError("Unsupported URL protocol."));
                return;
            }

            const transport = parsed.protocol === "https:"
                ? https
                : http;

            const requestOptions = {
                method: options.method || "GET",
                headers: {
                    "User-Agent": "ProtocolLab/1.0",
                    ...options.headers
                },
                timeout: this.timeout,
                rejectUnauthorized: true
            };

            const request = transport.request(
                parsed,
                requestOptions,
                response => {
                    const chunks = [];
                    let received = 0;

                    response.on("data", chunk => {
                        received += chunk.length;

                        if (received > this.maxResponseBytes) {
                            request.destroy(
                                new ProtocolError("Response size limit exceeded.")
                            );
                            return;
                        }

                        chunks.push(chunk);
                    });

                    response.on("end", () => {
                        resolve({
                            statusCode: response.statusCode,
                            headers: response.headers,
                            body: Buffer.concat(chunks).toString("utf8")
                        });
                    });
                }
            );

            request.on("timeout", () => {
                request.destroy(
                    new ProtocolError("HTTP request timed out.")
                );
            });

            request.on("error", reject);

            if (options.body !== undefined) {
                request.write(options.body);
            }

            request.end();
        });
    }
}

// ============================================================
// 6. SMTP state machine
// ============================================================

const SMTPState = Object.freeze({
    DISCONNECTED: "DISCONNECTED",
    CONNECTED: "CONNECTED",
    TLS_ACTIVE: "TLS_ACTIVE",
    AUTHENTICATED: "AUTHENTICATED",
    MAIL_ACCEPTED: "MAIL_ACCEPTED",
    CLOSED: "CLOSED"
});

class SMTPTransaction {
    constructor() {
        this.state = SMTPState.DISCONNECTED;
        this.sender = null;
        this.recipients = new Set();
    }

    transition(next) {
        const allowed = {
            DISCONNECTED: ["CONNECTED"],
            CONNECTED: ["TLS_ACTIVE", "CLOSED"],
            TLS_ACTIVE: ["AUTHENTICATED", "CLOSED"],
            AUTHENTICATED: ["MAIL_ACCEPTED", "CLOSED"],
            MAIL_ACCEPTED: ["CLOSED"],
            CLOSED: []
        };

        if (!allowed[this.state].includes(next)) {
            throw new ProtocolError(
                `Invalid SMTP transition: ${this.state} -> ${next}`
            );
        }

        this.state = next;
    }

    connect() {
        this.transition(SMTPState.CONNECTED);
    }

    startTLS() {
        this.transition(SMTPState.TLS_ACTIVE);
    }

    authenticate() {
        this.transition(SMTPState.AUTHENTICATED);
    }

    setSender(sender) {
        if (this.state !== SMTPState.AUTHENTICATED) {
            throw new ProtocolError("SMTP authentication required.");
        }

        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(sender)) {
            throw new ProtocolError("Invalid sender address.");
        }

        this.sender = sender;
    }

    addRecipient(recipient) {
        if (!this.sender) {
            throw new ProtocolError("MAIL FROM must precede RCPT TO.");
        }

        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(recipient)) {
            throw new ProtocolError("Invalid recipient address.");
        }

        this.recipients.add(recipient);
    }

    acceptMessage() {
        if (!this.sender || this.recipients.size === 0) {
            throw new ProtocolError("Incomplete SMTP transaction.");
        }

        this.transition(SMTPState.MAIL_ACCEPTED);
    }

    close() {
        this.transition(SMTPState.CLOSED);
    }
}

// ============================================================
// 7. FTP and SSH connection configuration
// ============================================================

function createFTPConfiguration({
    host,
    username,
    port = 21,
    secure = true
}) {
    return {
        host: validateHostname(host),
        username,
        port,
        protocol: secure ? "FTPS" : "FTP",
        encryption: secure ? "TLS" : "NONE",
        passiveMode: true
    };
}

function createSSHConfiguration({
    host,
    username,
    port = 22,
    hostKeyVerification = true
}) {
    if (!username || !/^[a-zA-Z0-9_.-]+$/.test(username)) {
        throw new ProtocolError("Invalid SSH username.");
    }

    if (!Number.isInteger(port) || port < 1 || port > 65535) {
        throw new ProtocolError("Invalid SSH port.");
    }

    if (!hostKeyVerification) {
        throw new ProtocolError(
            "SSH host-key verification must remain enabled."
        );
    }

    return Object.freeze({
        host: validateHostname(host),
        username,
        port,
        hostKeyVerification,
        authentication: "PUBLIC_KEY_OR_AGENT",
        encryption: "REQUIRED"
    });
}

// ============================================================
// 8. TCP connectivity diagnostics
// ============================================================

function checkTCPConnection(host, port, timeout = 3000) {
    return new Promise(resolve => {
        const socket = net.createConnection({
            host: validateHostname(host),
            port
        });

        let completed = false;

        function finish(result) {
            if (completed) return;

            completed = true;
            socket.destroy();
            resolve(result);
        }

        socket.setTimeout(timeout);

        socket.once("connect", () => {
            finish({
                reachable: true,
                host,
                port
            });
        });

        socket.once("timeout", () => {
            finish({
                reachable: false,
                reason: "Connection timeout"
            });
        });

        socket.once("error", error => {
            finish({
                reachable: false,
                reason: error.code || error.message
            });
        });
    });
}

// ============================================================
// 9. Protocol orchestration
// ============================================================

class ProtocolApplication {
    constructor(policy) {
        this.policy = policy;
        this.monitor = new ProtocolMonitor();
        this.dns = new DNSResolver();
        this.web = new WebClient();

        this.monitor.on("protocol-failure", event => {
            process.stderr.write(
                `[PROTOCOL FAILURE] ${event.protocol}: ${event.operation}\n`
            );
        });
    }

    async execute(protocol, operation, callback, port) {
        const decision = this.policy.evaluate(protocol, port);

        if (!decision.allowed) {
            this.monitor.record({
                protocol,
                operation,
                success: false,
                reason: decision.reason
            });

            throw new ProtocolError(decision.reason, "POLICY_DENIED");
        }

        const start = process.hrtime.bigint();

        try {
            const result = await callback();

            this.monitor.record({
                protocol,
                operation,
                success: true,
                durationMs: Number(
                    process.hrtime.bigint() - start
                ) / 1e6
            });

            return result;
        } catch (error) {
            this.monitor.record({
                protocol,
                operation,
                success: false,
                error: error.message
            });

            throw error;
        }
    }

    report() {
        return this.monitor.report();
    }
}

// ============================================================
// 10. Executable demonstration and assertions
// ============================================================

async function main() {
    const policy = new NetworkPolicy({
        allowedProtocols: ["HTTPS", "DNS", "SSH", "SMTP"],
        requireEncryption: true
    });

    const application = new ProtocolApplication(policy);

    console.log("APPLICATION LAYER PROTOCOL LAB\n");

    console.log("Protocol registry:");

    for (const [name, definition] of ProtocolRegistry) {
        console.log(name, definition);
    }

    console.log("\nPolicy evaluation:");

    console.log(
        "HTTPS:",
        policy.evaluate("HTTPS", 443)
    );

    console.log(
        "HTTP:",
        policy.evaluate("HTTP", 80)
    );

    // Validate DNS.
    console.log("\nHostname validation:");

    console.log(validateHostname("example.com"));

    // Demonstrate SMTP state transitions.
    console.log("\nSMTP workflow:");

    const smtp = new SMTPTransaction();

    smtp.connect();
    smtp.startTLS();
    smtp.authenticate();
    smtp.setSender("sender@example.com");
    smtp.addRecipient("recipient@example.com");
    smtp.acceptMessage();

    console.log("SMTP state:", smtp.state);

    smtp.close();

    // Demonstrate SSH and FTP configuration.
    console.log("\nSSH configuration:");

    console.log(createSSHConfiguration({
        host: "server.example.com",
        username: "administrator"
    }));

    console.log("\nFTP configuration:");

    console.log(createFTPConfiguration({
        host: "files.example.com",
        username: "transfer-user",
        secure: true
    }));

    // Execute real DNS lookup.
    try {
        const result = await application.execute(
            "DNS",
            "resolve A record",
            () => application.dns.resolve("example.com", "A"),
            53
        );

        console.log("\nDNS response:", result);
    } catch (error) {
        console.log("\nDNS operation unavailable:", error.message);
    }

    // Verify policy rejection.
    try {
        await application.execute(
            "HTTP",
            "insecure request",
            async () => ({ status: 200 }),
            80
        );
    } catch (error) {
        console.log("\nExpected policy rejection:", error.message);
    }

    console.log("\nMonitoring report:");
    console.log(JSON.stringify(application.report(), null, 2));

    // Cryptographically random transaction identifier.
    console.log(
        "\nTransaction ID:",
        crypto.randomUUID()
    );
}

main().catch(error => {
    console.error("Application failure:", error.message);
    process.exitCode = 1;
});
