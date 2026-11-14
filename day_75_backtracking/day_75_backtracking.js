'use strict';

/**
 * BACKTRACKING: EVENT-DRIVEN STATE SPACE EXPLORATION
 *
 * Node.js 18+
 * No third-party dependencies.
 *
 * Distinct engineering approach:
 * - Generator-based search.
 * - Asynchronous consumption.
 * - AbortSignal cancellation.
 * - Event-driven search monitoring.
 * - Explicit search policies.
 * - Duplicate-aware permutation and combination enumeration.
 * - Bitmask-based N-Queens.
 */

const { EventEmitter } = require('node:events');
const { performance } = require('node:perf_hooks');


class SearchError extends Error {}

class SearchLimitError extends SearchError {}

class SearchCancelledError extends SearchError {}


class SearchPolicy {
    constructor({
        maxNodes = 1_000_000,
        maxSolutions = 100_000,
        yieldEvery = 1000
    } = {}) {
        for (const [name, value] of Object.entries({
            maxNodes,
            maxSolutions,
            yieldEvery
        })) {
            if (!Number.isSafeInteger(value) || value < 1) {
                throw new TypeError(`${name} must be a positive safe integer`);
            }
        }

        this.maxNodes = maxNodes;
        this.maxSolutions = maxSolutions;
        this.yieldEvery = yieldEvery;

        Object.freeze(this);
    }
}


class SearchSession extends EventEmitter {
    constructor(policy = new SearchPolicy(), signal = null) {
        super();

        this.policy = policy;
        this.signal = signal;

        this.nodes = 0;
        this.solutions = 0;
        this.pruned = 0;
        this.maximumDepth = 0;

        this.startedAt = performance.now();
        this.finished = false;
    }

    visit(depth) {
        if (this.signal?.aborted) {
            throw new SearchCancelledError('Search was cancelled');
        }

        this.nodes++;

        if (this.nodes > this.policy.maxNodes) {
            throw new SearchLimitError('Maximum node count exceeded');
        }

        this.maximumDepth = Math.max(this.maximumDepth, depth);

        this.emit('node', {
            nodes: this.nodes,
            depth
        });
    }

    recordSolution(solution) {
        if (this.signal?.aborted) {
            throw new SearchCancelledError('Search was cancelled');
        }

        if (this.solutions >= this.policy.maxSolutions) {
            throw new SearchLimitError('Maximum solution count exceeded');
        }

        this.solutions++;

        this.emit('solution', {
            index: this.solutions,
            solution
        });
    }

    prune(reason) {
        this.pruned++;
        this.emit('pruned', { reason });
    }

    finish(status = 'completed') {
        if (this.finished) return;

        this.finished = true;

        this.emit('finished', {
            status,
            nodes: this.nodes,
            solutions: this.solutions,
            pruned: this.pruned,
            maximumDepth: this.maximumDepth,
            elapsedMilliseconds: Number(
                (performance.now() - this.startedAt).toFixed(3)
            )
        });
    }
}


/**
 * Asynchronously consume a synchronous generator.
 *
 * Periodic yielding prevents a large search from monopolizing
 * the Node.js event loop.
 */
async function consume(generator, session) {
    const results = [];
    let status = 'completed';

    try {
        for (const solution of generator) {
            results.push(solution);

            if (
                session.nodes % session.policy.yieldEvery === 0
            ) {
                await new Promise(resolve => setImmediate(resolve));
            }

            if (session.signal?.aborted) {
                throw new SearchCancelledError('Search was cancelled');
            }
        }
    } catch (error) {
        status = error instanceof SearchCancelledError
            ? 'cancelled'
            : error instanceof SearchLimitError
                ? 'limit_exceeded'
                : 'failed';

        throw error;
    } finally {
        session.finish(status);
    }

    return results;
}


function validateArray(values) {
    if (!Array.isArray(values)) {
        throw new TypeError('Input must be an array');
    }

    if (values.length > 20) {
        throw new RangeError('Input length cannot exceed 20');
    }

    // Stable sorting requires an explicit comparator.
    return [...values].sort((a, b) => {
        if (typeof a !== typeof b) {
            throw new TypeError('Mixed input types are not supported');
        }

        if (a < b) return -1;
        if (a > b) return 1;
        return 0;
    });
}


function* permutations(values, session) {
    const sorted = validateArray(values);
    const used = new Uint8Array(sorted.length);
    const path = [];

    function* search() {
        session.visit(path.length);

        if (path.length === sorted.length) {
            const result = [...path];
            session.recordSolution(result);
            yield result;
            return;
        }

        for (let i = 0; i < sorted.length; i++) {
            if (used[i]) continue;

            if (
                i > 0 &&
                sorted[i] === sorted[i - 1] &&
                !used[i - 1]
            ) {
                session.prune('duplicate permutation');
                continue;
            }

            used[i] = 1;
            path.push(sorted[i]);

            yield* search();

            path.pop();
            used[i] = 0;
        }
    }

    yield* search();
}


function* combinations(values, k, session) {
    const sorted = validateArray(values);

    if (!Number.isInteger(k) || k < 0 || k > sorted.length) {
        throw new RangeError('Invalid combination size');
    }

    const path = [];

    function* search(start) {
        session.visit(path.length);

        if (path.length === k) {
            const result = [...path];
            session.recordSolution(result);
            yield result;
            return;
        }

        const required = k - path.length;
        const last = sorted.length - required;

        for (let i = start; i <= last; i++) {
            if (
                i > start &&
                sorted[i] === sorted[i - 1]
            ) {
                session.prune('duplicate combination');
                continue;
            }

            path.push(sorted[i]);

            yield* search(i + 1);

            path.pop();
        }
    }

    yield* search(0);
}


/**
 * N-Queens using integer bitmasks.
 *
 * Every row is assigned exactly one queen.
 * The available bit positions are computed in constant time.
 */
function* nQueens(n, session) {
    if (!Number.isInteger(n) || n < 1 || n > 15) {
        throw new RangeError('Board size must be between 1 and 15');
    }

    const full = (1 << n) - 1;
    const positions = Array(n).fill(-1);

    function* search(row, columns, left, right) {
        session.visit(row);

        if (row === n) {
            const solution = [...positions];
            session.recordSolution(solution);
            yield solution;
            return;
        }

        let available = full & ~(columns | left | right);

        while (available !== 0) {
            const bit = available & -available;
            available ^= bit;

            const column = 31 - Math.clz32(bit);
            positions[row] = column;

            yield* search(
                row + 1,
                columns | bit,
                ((left | bit) << 1) & full,
                (right | bit) >> 1
            );

            positions[row] = -1;
        }
    }

    yield* search(0, 0, 0, 0);
}


function renderBoard(positions) {
    const n = positions.length;

    return positions.map(column => {
        const row = Array(n).fill('.');
        row[column] = 'Q';
        return row.join('');
    });
}


async function runDemonstration() {
    const policy = new SearchPolicy({
        maxNodes: 100_000,
        maxSolutions: 10_000,
        yieldEvery: 100
    });

    const permutationSession = new SearchSession(policy);

    permutationSession.on('solution', event => {
        if (event.index === 1) {
            console.log('First permutation:', event.solution);
        }
    });

    const permutationResults = await consume(
        permutations([1, 2, 2], permutationSession),
        permutationSession
    );

    console.log('Distinct permutations:', permutationResults.length);

    const combinationSession = new SearchSession(policy);

    const combinationResults = await consume(
        combinations([1, 2, 3, 4], 2, combinationSession),
        combinationSession
    );

    console.log('\nCombinations:', combinationResults);

    const queenSession = new SearchSession(policy);

    queenSession.on('finished', event => {
        console.log('\nN-Queens statistics:', event);
    });

    const queenResults = await consume(
        nQueens(4, queenSession),
        queenSession
    );

    console.log('\nN-Queens solutions:', queenResults.length);

    queenResults.forEach((solution, index) => {
        console.log(`\nSolution ${index + 1}`);
        console.log(renderBoard(solution).join('\n'));
    });

    if (
        permutationResults.length !== 3 ||
        combinationResults.length !== 6 ||
        queenResults.length !== 2
    ) {
        throw new Error('Algorithm validation failed');
    }

    console.log('\nAll demonstrations passed.');
}


/**
 * Demonstrates controlled cancellation.
 */
async function demonstrateCancellation() {
    const controller = new AbortController();

    const session = new SearchSession(
        new SearchPolicy({
            maxNodes: 100_000,
            maxSolutions: 10_000,
            yieldEvery: 1
        }),
        controller.signal
    );

    session.on('node', event => {
        if (event.nodes >= 10) {
            controller.abort();
        }
    });

    try {
        await consume(
            nQueens(8, session),
            session
        );
    } catch (error) {
        if (!(error instanceof SearchCancelledError)) {
            throw error;
        }

        console.log('\nCancellation handled:', error.message);
    }
}


async function main() {
    try {
        await runDemonstration();
        await demonstrateCancellation();
    } catch (error) {
        console.error('Search failure:', error.message);
        process.exitCode = 1;
    }
}


if (require.main === module) {
    main();
}


module.exports = {
    SearchPolicy,
    SearchSession,
    permutations,
    combinations,
    nQueens,
    renderBoard
};
