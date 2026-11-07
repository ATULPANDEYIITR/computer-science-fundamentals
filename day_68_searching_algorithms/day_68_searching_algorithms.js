"use strict";

const { EventEmitter } = require("node:events");
const { performance } = require("node:perf_hooks");

const Algorithm = Object.freeze({
    LINEAR: "Linear Search",
    BINARY: "Binary Search",
    INTERPOLATION: "Interpolation Search"
});

class SearchValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "SearchValidationError";
    }
}

class SearchResult {
    constructor(algorithm, target, index, comparisons, elapsedMs) {
        this.algorithm = algorithm;
        this.target = target;
        this.index = index;
        this.comparisons = comparisons;
        this.elapsedMs = elapsedMs;
        Object.freeze(this);
    }

    get found() {
        return this.index !== null;
    }
}

class SearchService extends EventEmitter {
    constructor() {
        super();
        this.statistics = new Map(
            Object.values(Algorithm).map(name => [
                name,
                { searches: 0, matches: 0, comparisons: 0 }
            ])
        );
    }

    static validateData(data) {
        if (!Array.isArray(data)) {
            throw new SearchValidationError("Data must be an array.");
        }

        if (!data.every(Number.isSafeInteger)) {
            throw new SearchValidationError(
                "All elements must be safe integers."
            );
        }
    }

    static validateTarget(target) {
        if (!Number.isSafeInteger(target)) {
            throw new SearchValidationError(
                "Target must be a safe integer."
            );
        }
    }

    static validateSorted(data) {
        for (let i = 1; i < data.length; i++) {
            if (data[i] < data[i - 1]) {
                throw new SearchValidationError(
                    "This algorithm requires ascending sorted data."
                );
            }
        }
    }

    execute(algorithm, data, target) {
        SearchService.validateData(data);
        SearchService.validateTarget(target);

        if (algorithm !== Algorithm.LINEAR) {
            SearchService.validateSorted(data);
        }

        const start = performance.now();
        let index = null;
        let comparisons = 0;

        switch (algorithm) {
            case Algorithm.LINEAR: {
                for (let i = 0; i < data.length; i++) {
                    comparisons++;

                    if (data[i] === target) {
                        index = i;
                        break;
                    }
                }
                break;
            }

            case Algorithm.BINARY: {
                let left = 0;
                let right = data.length - 1;

                while (left <= right) {
                    const middle = left + Math.floor((right - left) / 2);
                    comparisons++;

                    if (data[middle] === target) {
                        index = middle;
                        right = middle - 1;
                    } else if (data[middle] < target) {
                        left = middle + 1;
                    } else {
                        right = middle - 1;
                    }
                }
                break;
            }

            case Algorithm.INTERPOLATION: {
                let low = 0;
                let high = data.length - 1;

                while (low <= high) {
                    comparisons++;

                    if (target < data[low] || target > data[high]) {
                        break;
                    }

                    if (data[low] === data[high]) {
                        if (data[low] === target) {
                            index = low;
                        }
                        break;
                    }

                    const numerator =
                        BigInt(target - data[low]) * BigInt(high - low);

                    const denominator = BigInt(data[high] - data[low]);

                    let position = low +
                        Number(numerator / denominator);

                    position = Math.max(low, Math.min(position, high));

                    comparisons++;

                    if (data[position] === target) {
                        index = position;
                        high = position - 1;
                    } else if (data[position] < target) {
                        low = position + 1;
                    } else {
                        high = position - 1;
                    }
                }
                break;
            }

            default:
                throw new SearchValidationError(
                    `Unknown search algorithm: ${algorithm}`
                );
        }

        const elapsedMs = performance.now() - start;

        const result = new SearchResult(
            algorithm,
            target,
            index,
            comparisons,
            elapsedMs
        );

        this.updateStatistics(result);
        this.emit("searchCompleted", result);

        return result;
    }

    updateStatistics(result) {
        const stats = this.statistics.get(result.algorithm);

        stats.searches++;
        stats.matches += result.found ? 1 : 0;
        stats.comparisons += result.comparisons;
    }

    getStatistics() {
        return Object.fromEntries(
            [...this.statistics.entries()].map(([name, values]) => [
                name,
                { ...values }
            ])
        );
    }

    resetStatistics() {
        for (const stats of this.statistics.values()) {
            stats.searches = 0;
            stats.matches = 0;
            stats.comparisons = 0;
        }
    }
}

class InventoryIndex {
    constructor(productIds = []) {
        SearchService.validateData(productIds);

        this.productIds = [...productIds].sort((a, b) => a - b);
        this.searchService = new SearchService();
    }

    find(productId) {
        return this.searchService.execute(
            Algorithm.BINARY,
            this.productIds,
            productId
        );
    }

    insert(productId) {
        SearchService.validateTarget(productId);

        // Binary insertion preserves sorted order.
        let left = 0;
        let right = this.productIds.length;

        while (left < right) {
            const middle = left + Math.floor((right - left) / 2);

            if (this.productIds[middle] < productId) {
                left = middle + 1;
            } else {
                right = middle;
            }
        }

        this.productIds.splice(left, 0, productId);
    }

    remove(productId) {
        const result = this.searchService.execute(
            Algorithm.BINARY,
            this.productIds,
            productId
        );

        if (!result.found) {
            return false;
        }

        this.productIds.splice(result.index, 1);
        return true;
    }
}

function runTests(service) {
    const data = [10, 20, 30, 40, 50, 60];

    console.assert(
        service.execute(Algorithm.LINEAR, data, 40).index === 3
    );

    console.assert(
        service.execute(Algorithm.BINARY, data, 40).index === 3
    );

    console.assert(
        service.execute(Algorithm.INTERPOLATION, data, 40).index === 3
    );

    const duplicates = [5, 5, 5, 10, 10, 20];

    console.assert(
        service.execute(Algorithm.BINARY, duplicates, 10).index === 3
    );

    console.assert(
        service.execute(Algorithm.INTERPOLATION, duplicates, 10).index === 3
    );

    console.assert(
        service.execute(Algorithm.BINARY, [], 10).index === null
    );

    console.assert(
        service.execute(Algorithm.INTERPOLATION, [7, 7, 7], 7).index === 0
    );

    let rejected = false;

    try {
        service.execute(Algorithm.BINARY, [10, 5, 20], 5);
    } catch (error) {
        rejected = error instanceof SearchValidationError;
    }

    if (!rejected) {
        throw new Error("Sorted-data validation failed.");
    }

    rejected = false;

    try {
        service.execute(Algorithm.LINEAR, [1, 2, 3], 2.5);
    } catch (error) {
        rejected = true;
    }

    if (!rejected) {
        throw new Error("Target validation failed.");
    }

    const inventory = new InventoryIndex([1005, 1001, 1003]);

    console.assert(inventory.find(1003).index === 1);

    inventory.insert(1002);
    console.assert(
        JSON.stringify(inventory.productIds) ===
        JSON.stringify([1001, 1002, 1003, 1005])
    );

    console.assert(inventory.remove(1002));
    console.assert(!inventory.remove(9999));

    console.log("All JavaScript tests passed.");
}

async function runBatchSearch(service, data, targets) {
    // Promise-based interface for independent search requests.
    const results = await Promise.all(
        targets.map(target =>
            Promise.resolve().then(() =>
                service.execute(Algorithm.BINARY, data, target)
            )
        )
    );

    return results;
}

async function main() {
    const service = new SearchService();

    service.on("searchCompleted", result => {
        console.log(
            `[EVENT] ${result.algorithm}: target=${result.target}, ` +
            `index=${result.index}, comparisons=${result.comparisons}`
        );
    });

    const data = [12, 24, 36, 48, 60, 72, 84, 96];

    console.log("SEARCHING ALGORITHMS");
    console.log("Dataset:", data);

    for (const algorithm of Object.values(Algorithm)) {
        const result = service.execute(algorithm, data, 60);

        console.log({
            algorithm: result.algorithm,
            found: result.found,
            index: result.index,
            comparisons: result.comparisons,
            elapsedMs: result.elapsedMs.toFixed(5)
        });
    }

    console.log("\nBatch search:");

    const batch = await runBatchSearch(service, data, [12, 48, 96, 100]);

    for (const result of batch) {
        console.log(
            `Target ${result.target}: ${result.found ? result.index : "Not found"}`
        );
    }

    console.log("\nInventory:");

    const inventory = new InventoryIndex([5004, 5001, 5003, 5002]);
    console.log(inventory.find(5003));
    inventory.insert(5005);
    inventory.remove(5001);
    console.log("Current inventory:", inventory.productIds);

    console.log("\nStatistics:");
    console.table(service.getStatistics());

    console.log("\nValidation:");
    runTests(service);
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
