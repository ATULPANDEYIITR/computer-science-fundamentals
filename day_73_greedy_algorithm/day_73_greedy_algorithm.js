"use strict";

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");

class GreedyAlgorithmError extends Error {
    constructor(message) {
        super(message);
        this.name = "GreedyAlgorithmError";
    }
}

function requireFiniteNumber(value, name, minimum = 0) {
    if (
        typeof value !== "number" ||
        !Number.isFinite(value) ||
        value < minimum
    ) {
        throw new GreedyAlgorithmError(
            `${name} must be a finite number >= ${minimum}.`
        );
    }
}

class Activity {
    constructor(id, start, finish) {
        if (typeof id !== "string" || id.trim() === "") {
            throw new GreedyAlgorithmError("Invalid activity ID.");
        }

        requireFiniteNumber(start, "Start");
        requireFiniteNumber(finish, "Finish");

        if (finish <= start) {
            throw new GreedyAlgorithmError(
                "Finish must be greater than start."
            );
        }

        this.id = id;
        this.start = start;
        this.finish = finish;

        Object.freeze(this);
    }
}

class ActivityScheduler extends EventEmitter {
    constructor() {
        super();
        this.executionHistory = [];
    }

    schedule(activities) {
        if (!Array.isArray(activities)) {
            throw new GreedyAlgorithmError(
                "Activities must be an array."
            );
        }

        const ids = new Set();

        for (const activity of activities) {
            if (!(activity instanceof Activity)) {
                throw new GreedyAlgorithmError(
                    "Every entry must be an Activity."
                );
            }

            if (ids.has(activity.id)) {
                throw new GreedyAlgorithmError(
                    `Duplicate activity: ${activity.id}`
                );
            }

            ids.add(activity.id);
        }

        // Sorting by finish time implements the greedy-choice rule.
        const ordered = [...activities].sort(
            (a, b) =>
                a.finish - b.finish ||
                a.start - b.start ||
                a.id.localeCompare(b.id)
        );

        let lastFinish = -1;
        const selected = [];
        const rejected = [];

        for (const activity of ordered) {
            if (activity.start >= lastFinish) {
                selected.push(activity);
                lastFinish = activity.finish;

                this.emit("selected", activity);
            } else {
                rejected.push(activity);
                this.emit("rejected", activity);
            }
        }

        const result = Object.freeze({
            selected: Object.freeze(selected),
            rejected: Object.freeze(rejected),
            count: selected.length
        });

        this.executionHistory.push(result);
        this.emit("completed", result);

        return result;
    }
}

class MinHeap {
    constructor(compare) {
        this.values = [];
        this.compare = compare;
    }

    get size() {
        return this.values.length;
    }

    push(value) {
        this.values.push(value);

        let index = this.size - 1;

        while (index > 0) {
            const parent = Math.floor((index - 1) / 2);

            if (
                this.compare(
                    this.values[parent],
                    this.values[index]
                ) <= 0
            ) {
                break;
            }

            [this.values[parent], this.values[index]] =
                [this.values[index], this.values[parent]];

            index = parent;
        }
    }

    pop() {
        if (this.size === 0) {
            throw new GreedyAlgorithmError("Heap is empty.");
        }

        const minimum = this.values[0];
        const last = this.values.pop();

        if (this.size > 0) {
            this.values[0] = last;

            let index = 0;

            while (true) {
                const left = index * 2 + 1;
                const right = left + 1;
                let smallest = index;

                if (
                    left < this.size &&
                    this.compare(
                        this.values[left],
                        this.values[smallest]
                    ) < 0
                ) {
                    smallest = left;
                }

                if (
                    right < this.size &&
                    this.compare(
                        this.values[right],
                        this.values[smallest]
                    ) < 0
                ) {
                    smallest = right;
                }

                if (smallest === index) break;

                [this.values[index], this.values[smallest]] =
                    [this.values[smallest], this.values[index]];

                index = smallest;
            }
        }

        return minimum;
    }
}

class HuffmanCodec {
    constructor(frequencies) {
        if (
            !(frequencies instanceof Map) ||
            frequencies.size === 0
        ) {
            throw new GreedyAlgorithmError(
                "A nonempty frequency Map is required."
            );
        }

        for (const [symbol, frequency] of frequencies) {
            if (typeof symbol !== "string" || symbol.length !== 1) {
                throw new GreedyAlgorithmError(
                    "Symbols must be single characters."
                );
            }

            if (
                !Number.isSafeInteger(frequency) ||
                frequency <= 0
            ) {
                throw new GreedyAlgorithmError(
                    "Frequencies must be positive safe integers."
                );
            }
        }

        this.frequencies = new Map(frequencies);
        this.codes = new Map();

        this.root = this.buildTree();
        this.generateCodes(this.root, "");
    }

    buildTree() {
        let serial = 0;

        const heap = new MinHeap((a, b) =>
            a.frequency - b.frequency ||
            a.serial - b.serial
        );

        const entries = [...this.frequencies.entries()]
            .sort(([a], [b]) => a.localeCompare(b));

        for (const [symbol, frequency] of entries) {
            heap.push({
                symbol,
                frequency,
                serial: serial++,
                left: null,
                right: null
            });
        }

        while (heap.size > 1) {
            const left = heap.pop();
            const right = heap.pop();

            const total = left.frequency + right.frequency;

            if (!Number.isSafeInteger(total)) {
                throw new GreedyAlgorithmError(
                    "Combined frequency exceeds safe integer range."
                );
            }

            heap.push({
                symbol: null,
                frequency: total,
                serial: serial++,
                left,
                right
            });
        }

        return heap.pop();
    }

    generateCodes(node, prefix) {
        if (node.symbol !== null) {
            this.codes.set(node.symbol, prefix || "0");
            return;
        }

        this.generateCodes(node.left, prefix + "0");
        this.generateCodes(node.right, prefix + "1");
    }

    encode(message) {
        if (typeof message !== "string") {
            throw new GreedyAlgorithmError(
                "Message must be a string."
            );
        }

        let encoded = "";

        for (const character of message) {
            const code = this.codes.get(character);

            if (code === undefined) {
                throw new GreedyAlgorithmError(
                    `Unknown symbol: ${character}`
                );
            }

            encoded += code;
        }

        return encoded;
    }

    decode(bits) {
        if (
            typeof bits !== "string" ||
            !/^[01]*$/.test(bits)
        ) {
            throw new GreedyAlgorithmError(
                "Encoded input must contain only binary digits."
            );
        }

        if (this.root.symbol !== null) {
            return this.root.symbol.repeat(bits.length);
        }

        const result = [];
        let node = this.root;

        for (const bit of bits) {
            node = bit === "0" ? node.left : node.right;

            if (!node) {
                throw new GreedyAlgorithmError(
                    "Invalid encoded sequence."
                );
            }

            if (node.symbol !== null) {
                result.push(node.symbol);
                node = this.root;
            }
        }

        if (node !== this.root) {
            throw new GreedyAlgorithmError(
                "Incomplete Huffman codeword."
            );
        }

        return result.join("");
    }

    getWeightedPathLength() {
        let total = 0;

        for (const [symbol, frequency] of this.frequencies) {
            total += frequency * this.codes.get(symbol).length;
        }

        return total;
    }
}

class FractionalKnapsack {
    static solve(items, capacity) {
        requireFiniteNumber(capacity, "Capacity");

        if (!Array.isArray(items)) {
            throw new GreedyAlgorithmError("Items must be an array.");
        }

        const ids = new Set();

        const validated = items.map(item => {
            if (!item || typeof item.id !== "string" || !item.id) {
                throw new GreedyAlgorithmError("Invalid item ID.");
            }

            if (ids.has(item.id)) {
                throw new GreedyAlgorithmError("Duplicate item ID.");
            }

            ids.add(item.id);

            requireFiniteNumber(item.value, "Value");

            if (
                typeof item.weight !== "number" ||
                !Number.isFinite(item.weight) ||
                item.weight <= 0
            ) {
                throw new GreedyAlgorithmError(
                    "Weight must be finite and positive."
                );
            }

            return {
                ...item,
                ratio: item.value / item.weight
            };
        });

        validated.sort(
            (a, b) =>
                b.ratio - a.ratio ||
                a.id.localeCompare(b.id)
        );

        let remaining = capacity;
        let totalValue = 0;
        const selected = [];

        for (const item of validated) {
            if (remaining <= 0) break;

            const fraction = Math.min(
                1,
                remaining / item.weight
            );

            if (fraction <= 0) continue;

            const weight = fraction * item.weight;
            const value = fraction * item.value;

            selected.push({
                id: item.id,
                fraction,
                weight,
                value
            });

            remaining = Math.max(0, remaining - weight);
            totalValue += value;
        }

        return {
            selected,
            totalValue,
            usedCapacity: capacity - remaining,
            remainingCapacity: remaining
        };
    }
}

// Demonstrates an asynchronous workflow with independent validation.
async function executeOptimization(scheduler, activities) {
    await new Promise(resolve => setImmediate(resolve));

    return scheduler.schedule(activities);
}

async function runTests() {
    const scheduler = new ActivityScheduler();

    const result = scheduler.schedule([
        new Activity("A", 1, 3),
        new Activity("B", 3, 5),
        new Activity("C", 2, 4)
    ]);

    console.assert(result.count === 2);
    console.assert(
        result.selected.map(x => x.id).join(",") === "A,B"
    );

    const knapsack = FractionalKnapsack.solve([
        { id: "A", value: 60, weight: 10 },
        { id: "B", value: 100, weight: 20 },
        { id: "C", value: 120, weight: 30 }
    ], 50);

    console.assert(Math.abs(knapsack.totalValue - 240) < 1e-9);

    const codec = new HuffmanCodec(
        new Map([
            ["a", 45],
            ["b", 13],
            ["c", 12],
            ["d", 16],
            ["e", 9],
            ["f", 5]
        ])
    );

    const message = "abcdef";
    console.assert(codec.decode(codec.encode(message)) === message);

    const single = new HuffmanCodec(new Map([["x", 5]]));
    console.assert(single.decode(single.encode("xxxxx")) === "xxxxx");

    let failed = false;

    try {
        codec.encode("z");
    } catch (error) {
        failed = error instanceof GreedyAlgorithmError;
    }

    console.assert(failed);

    console.log("All JavaScript tests passed.");
}

async function main() {
    await runTests();

    const scheduler = new ActivityScheduler();

    scheduler.on("selected", activity => {
        console.log(`Selected activity: ${activity.id}`);
    });

    scheduler.on("rejected", activity => {
        console.log(`Rejected activity: ${activity.id}`);
    });

    const activities = [
        new Activity("A101", 1, 4),
        new Activity("A102", 3, 5),
        new Activity("A103", 0, 6),
        new Activity("A104", 5, 7),
        new Activity("A105", 8, 9),
        new Activity("A106", 5, 9),
        new Activity("A107", 2, 3)
    ];

    const activityResult = await executeOptimization(
        scheduler,
        activities
    );

    const knapsackResult = FractionalKnapsack.solve([
        { id: "Gold", value: 60, weight: 10 },
        { id: "Silver", value: 100, weight: 20 },
        { id: "Copper", value: 120, weight: 30 }
    ], 50);

    const message = "greedy algorithms";
    const frequencies = new Map();

    for (const character of message) {
        frequencies.set(
            character,
            (frequencies.get(character) || 0) + 1
        );
    }

    const codec = new HuffmanCodec(frequencies);
    const encoded = codec.encode(message);

    const report = {
        activitySelection: {
            selected: activityResult.selected.map(a => a.id),
            rejected: activityResult.rejected.map(a => a.id)
        },
        fractionalKnapsack: knapsackResult,
        huffman: {
            codes: Object.fromEntries(codec.codes),
            encoded,
            decoded: codec.decode(encoded),
            weightedPathLength: codec.getWeightedPathLength()
        }
    };

    const json = JSON.stringify(report, null, 2);

    console.log("\nOptimization report:\n" + json);

    try {
        await fs.writeFile(
            "greedy_algorithm_report.json",
            json,
            { encoding: "utf8", mode: 0o600 }
        );

        console.log("Report saved successfully.");
    } catch (error) {
        console.error("Report persistence failed:", error.message);
        process.exitCode = 1;
    }
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
