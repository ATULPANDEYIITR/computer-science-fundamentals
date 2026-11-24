"use strict";

/*
 * Network Layer Engineering
 * IPv4, IPv6, CIDR, subnetting and event-driven routing.
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 */

const net = require("node:net");
const fs = require("node:fs/promises");
const EventEmitter = require("node:events");

class NetworkError extends Error {}
class ValidationError extends NetworkError {}
class RouteNotFoundError extends NetworkError {}

const Family = Object.freeze({
    IPV4: 4,
    IPV6: 6
});

function validateAddress(address) {
    if (typeof address !== "string" || net.isIP(address) === 0) {
        throw new ValidationError(`Invalid IP address: ${address}`);
    }

    return {
        address,
        family: net.isIP(address)
    };
}

function ipv4ToBigInt(address) {
    const parts = address.split(".");

    if (parts.length !== 4) {
        throw new ValidationError("Invalid IPv4 address");
    }

    return parts.reduce((value, part) => {
        return (value << 8n) | BigInt(Number(part));
    }, 0n);
}

function ipv6ToBigInt(address) {
    if (net.isIP(address) !== 6) {
        throw new ValidationError("Invalid IPv6 address");
    }

    let input = address.toLowerCase();

    // Convert an embedded IPv4 address into two hexadecimal groups.
    if (input.includes(".")) {
        const lastColon = input.lastIndexOf(":");
        const ipv4 = input.slice(lastColon + 1);
        const value = ipv4ToBigInt(ipv4);

        const first = Number((value >> 16n) & 65535n);
        const second = Number(value & 65535n);

        input = input.slice(0, lastColon) +
            ":" + first.toString(16) +
            ":" + second.toString(16);
    }

    const halves = input.split("::");

    let groups;

    if (halves.length === 2) {
        const left = halves[0] ? halves[0].split(":") : [];
        const right = halves[1] ? halves[1].split(":") : [];
        const missing = 8 - left.length - right.length;

        if (missing < 1) {
            throw new ValidationError("Invalid IPv6 compression");
        }

        groups = [
            ...left,
            ...Array(missing).fill("0"),
            ...right
        ];
    } else {
        groups = input.split(":");
    }

    if (groups.length !== 8) {
        throw new ValidationError("Invalid IPv6 groups");
    }

    return groups.reduce((value, group) => {
        return (value << 16n) | BigInt(parseInt(group, 16));
    }, 0n);
}

function addressToBigInt(address, family) {
    return family === Family.IPV4
        ? ipv4ToBigInt(address)
        : ipv6ToBigInt(address);
}

function parseCIDR(cidr) {
    if (typeof cidr !== "string" || !cidr.includes("/")) {
        throw new ValidationError("CIDR notation is required");
    }

    const [address, prefixText, ...extra] = cidr.split("/");

    if (extra.length !== 0 || !/^\d+$/.test(prefixText)) {
        throw new ValidationError("Malformed CIDR notation");
    }

    const parsed = validateAddress(address);
    const prefix = Number(prefixText);
    const bits = parsed.family === 4 ? 32 : 128;

    if (!Number.isInteger(prefix) || prefix < 0 || prefix > bits) {
        throw new ValidationError("Invalid prefix length");
    }

    const numericAddress = addressToBigInt(address, parsed.family);

    const hostBits = BigInt(bits - prefix);
    const mask = prefix === 0
        ? 0n
        : ((1n << BigInt(prefix)) - 1n) << hostBits;

    const network = numericAddress & mask;
    const size = 1n << hostBits;

    return {
        address,
        family: parsed.family,
        prefix,
        bits,
        mask,
        network,
        size,
        last: network + size - 1n
    };
}

function contains(cidr, address) {
    const network = parseCIDR(cidr);
    const parsed = validateAddress(address);

    if (parsed.family !== network.family) {
        return false;
    }

    const value = addressToBigInt(address, parsed.family);

    return value >= network.network && value <= network.last;
}

function analyzeSubnet(cidr) {
    const network = parseCIDR(cidr);

    return {
        cidr,
        family: network.family,
        prefix: network.prefix,
        totalAddresses: network.size.toString(),
        firstAddress: network.network.toString(),
        lastAddress: network.last.toString(),
        mask: network.mask.toString()
    };
}

function ipv4SubnetMask(prefix) {
    if (!Number.isInteger(prefix) || prefix < 0 || prefix > 32) {
        throw new ValidationError("Invalid IPv4 prefix");
    }

    const mask = prefix === 0
        ? 0n
        : (0xffffffffn << BigInt(32 - prefix)) & 0xffffffffn;

    return [24n, 16n, 8n, 0n]
        .map(shift => Number((mask >> shift) & 255n))
        .join(".");
}

function divideSubnet(cidr, newPrefix) {
    const parent = parseCIDR(cidr);

    if (newPrefix < parent.prefix || newPrefix > parent.bits) {
        throw new ValidationError("Invalid child subnet prefix");
    }

    const childSize = 1n << BigInt(parent.bits - newPrefix);
    const count = parent.size / childSize;

    // Prevent accidental creation of an enormous result array.
    if (count > 4096n) {
        throw new ValidationError(
            "Subnet expansion exceeds 4096 networks"
        );
    }

    const results = [];

    for (let index = 0n; index < count; index++) {
        const start = parent.network + index * childSize;

        results.push({
            start: start.toString(),
            prefix: newPrefix,
            size: childSize.toString()
        });
    }

    return results;
}

class NetworkInterface {
    constructor(name, address, mtu = 1500) {
        if (!name || typeof name !== "string") {
            throw new ValidationError("Interface name is required");
        }

        const [ip, prefix] = address.split("/");
        const parsed = validateAddress(ip);

        if (!Number.isInteger(Number(prefix)) ||
            Number(prefix) < 0 ||
            Number(prefix) > (parsed.family === 4 ? 32 : 128)) {
            throw new ValidationError("Invalid interface prefix");
        }

        if (!Number.isInteger(mtu) || mtu < 576 || mtu > 65535) {
            throw new ValidationError("Invalid MTU");
        }

        this.name = name;
        this.address = address;
        this.family = parsed.family;
        this.mtu = mtu;
        this.enabled = true;
    }
}

class Router extends EventEmitter {
    constructor() {
        super();
        this.interfaces = new Map();
        this.routes = [];
        this.packetCount = 0;
    }

    addInterface(networkInterface) {
        if (this.interfaces.has(networkInterface.name)) {
            throw new NetworkError("Duplicate interface");
        }

        this.interfaces.set(
            networkInterface.name,
            networkInterface
        );

        this.emit("interface:added", {
            name: networkInterface.name
        });
    }

    addRoute({
        destination,
        interfaceName,
        nextHop = null,
        metric = 100
    }) {
        const network = parseCIDR(destination);
        const outgoing = this.interfaces.get(interfaceName);

        if (!outgoing) {
            throw new ValidationError("Unknown interface");
        }

        if (!outgoing.enabled) {
            throw new NetworkError("Interface is disabled");
        }

        if (network.family !== outgoing.family) {
            throw new ValidationError(
                "Route and interface address families differ"
            );
        }

        if (!Number.isSafeInteger(metric) || metric < 0) {
            throw new ValidationError("Invalid route metric");
        }

        if (nextHop !== null) {
            const gateway = validateAddress(nextHop);

            if (gateway.family !== network.family) {
                throw new ValidationError("Gateway family mismatch");
            }
        }

        const route = Object.freeze({
            destination,
            interfaceName,
            nextHop,
            metric,
            active: true
        });

        this.routes.push(route);

        this.emit("route:added", route);
    }

    findRoute(destination) {
        const target = validateAddress(destination);

        const matches = this.routes.filter(route => {
            const network = parseCIDR(route.destination);

            return route.active &&
                network.family === target.family &&
                contains(route.destination, destination) &&
                this.interfaces.get(route.interfaceName)?.enabled;
        });

        if (matches.length === 0) {
            throw new RouteNotFoundError(
                `No route to ${destination}`
            );
        }

        // Longest prefix first; lowest metric breaks ties.
        matches.sort((a, b) => {
            const prefixDifference =
                parseCIDR(b.destination).prefix -
                parseCIDR(a.destination).prefix;

            return prefixDifference || a.metric - b.metric;
        });

        return matches[0];
    }

    async forwardPacket(packet) {
        const { source, destination, payloadBytes = 0 } = packet;

        const sourceInfo = validateAddress(source);
        const destinationInfo = validateAddress(destination);

        if (sourceInfo.family !== destinationInfo.family) {
            throw new ValidationError("Address family mismatch");
        }

        if (!Number.isSafeInteger(payloadBytes) || payloadBytes < 0) {
            throw new ValidationError("Invalid packet payload size");
        }

        const route = this.findRoute(destination);
        const outgoing = this.interfaces.get(route.interfaceName);

        if (payloadBytes + 20 > outgoing.mtu &&
            outgoing.family === Family.IPV4) {
            throw new NetworkError(
                "Packet exceeds interface MTU"
            );
        }

        if (payloadBytes + 40 > outgoing.mtu &&
            outgoing.family === Family.IPV6) {
            throw new NetworkError(
                "Packet exceeds interface MTU"
            );
        }

        // Simulate asynchronous packet-processing latency.
        await new Promise(resolve => setImmediate(resolve));

        this.packetCount++;

        const result = {
            packetId: this.packetCount,
            source,
            destination,
            outgoingInterface: outgoing.name,
            nextHop: route.nextHop || destination,
            matchedNetwork: route.destination,
            metric: route.metric,
            state: "FORWARDED"
        };

        this.emit("packet:forwarded", result);

        return result;
    }

    setInterfaceState(name, enabled) {
        const networkInterface = this.interfaces.get(name);

        if (!networkInterface) {
            throw new ValidationError("Unknown interface");
        }

        networkInterface.enabled = Boolean(enabled);

        this.emit("interface:state", {
            name,
            enabled: networkInterface.enabled
        });
    }

    getStatistics() {
        return {
            packetCount: this.packetCount,
            interfaceCount: this.interfaces.size,
            routeCount: this.routes.length
        };
    }
}

async function main() {
    const router = new Router();

    router.on("route:added", route => {
        console.log("ROUTE ADDED:", route.destination);
    });

    router.on("packet:forwarded", packet => {
        console.log(
            `FORWARDED ${packet.packetId}:`,
            packet.destination,
            "via",
            packet.outgoingInterface
        );
    });

    router.on("interface:state", event => {
        console.log("INTERFACE STATE:", event);
    });

    console.log("IPv4 SUBNET");
    console.log(analyzeSubnet("192.168.1.0/24"));
    console.log("IPv4 MASK:", ipv4SubnetMask(26));

    console.log("\nIPv6 SUBNET");
    console.log(analyzeSubnet("2001:db8:1::/64"));

    console.log("\nSUBNET DIVISION");
    console.log(
        divideSubnet("192.168.1.0/24", 26)
    );

    router.addInterface(
        new NetworkInterface("eth0", "192.168.1.1/24")
    );

    router.addInterface(
        new NetworkInterface("eth1", "10.0.0.1/24")
    );

    router.addInterface(
        new NetworkInterface("eth2", "2001:db8:1::1/64")
    );

    router.addRoute({
        destination: "0.0.0.0/0",
        interfaceName: "eth1",
        nextHop: "10.0.0.254",
        metric: 200
    });

    router.addRoute({
        destination: "172.16.0.0/16",
        interfaceName: "eth1",
        nextHop: "10.0.0.2",
        metric: 50
    });

    router.addRoute({
        destination: "172.16.10.0/24",
        interfaceName: "eth1",
        nextHop: "10.0.0.3",
        metric: 10
    });

    router.addRoute({
        destination: "2001:db8:2::/64",
        interfaceName: "eth2",
        nextHop: "2001:db8:1::2"
    });

    const packet = await router.forwardPacket({
        source: "192.168.1.20",
        destination: "172.16.10.50",
        payloadBytes: 1200
    });

    if (packet.matchedNetwork !== "172.16.10.0/24") {
        throw new Error("Longest-prefix matching failed");
    }

    await router.forwardPacket({
        source: "2001:db8:1::10",
        destination: "2001:db8:2::20",
        payloadBytes: 1200
    });

    console.log("\nSTATISTICS");
    console.log(router.getStatistics());

    const report = {
        subnet: analyzeSubnet("192.168.1.0/24"),
        ipv6: analyzeSubnet("2001:db8:1::/64"),
        statistics: router.getStatistics(),
        routes: router.routes
    };

    await fs.writeFile(
        "network_report.json",
        JSON.stringify(report, null, 2),
        { encoding: "utf8", mode: 0o600 }
    );

    console.log("\nReport saved.");

    // Failure handling.
    try {
        validateAddress("192.168.1.999");
    } catch (error) {
        console.log("EXPECTED VALIDATION ERROR:", error.message);
    }

    try {
        router.findRoute("203.0.113.20");
    } catch (error) {
        console.log("EXPECTED ROUTING ERROR:", error.message);
    }

    router.setInterfaceState("eth1", false);

    try {
        await router.forwardPacket({
            source: "192.168.1.20",
            destination: "172.16.10.50"
        });
    } catch (error) {
        console.log("EXPECTED INTERFACE ERROR:", error.message);
    }
}

main().catch(error => {
    console.error("NETWORK FAILURE:", error.message);
    process.exitCode = 1;
});
