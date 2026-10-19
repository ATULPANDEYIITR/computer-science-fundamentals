'use strict';

/*
 * Functions and Abstraction
 *
 * This implementation emphasizes JavaScript-specific function behavior:
 * callbacks, closures, higher-order functions, generators, promises,
 * async/await, event-driven processing, and class-based domain boundaries.
 */

const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');

function section(title) {
    console.log(`\n${'='.repeat(72)}\n${title}\n${'='.repeat(72)}`);
}

function calculateDiscount(price, percentage) {
    if (!Number.isFinite(price) || price < 0) {
        throw new RangeError('price must be a non-negative finite number');
    }

    if (!Number.isFinite(percentage) || percentage < 0 || percentage > 100) {
        throw new RangeError('percentage must be between 0 and 100');
    }

    return price * percentage / 100;
}

function finalPrice(price, percentage) {
    return price - calculateDiscount(price, percentage);
}

function parseRepositoryName(input) {
    if (typeof input !== 'string') {
        throw new TypeError('repository name must be a string');
    }

    const name = input.trim().toLowerCase();

    if (!/^[a-z0-9][a-z0-9._-]*$/.test(name)) {
        throw new Error('repository name contains invalid characters');
    }

    return name;
}

function average(values) {
    if (!Array.isArray(values) || values.length === 0) {
        throw new RangeError('values must be a non-empty array');
    }

    if (!values.every(Number.isFinite)) {
        throw new TypeError('all values must be finite numbers');
    }

    return values.reduce((sum, value) => sum + value, 0) / values.length;
}

// JavaScript functions are first-class values, so behavior can be passed
// into a reusable function instead of being hard-coded into it.
function mapRecords(records, operation) {
    if (!Array.isArray(records)) {
        throw new TypeError('records must be an array');
    }

    if (typeof operation !== 'function') {
        throw new TypeError('operation must be a function');
    }

    return records.map(operation);
}

function filterRecords(records, predicate) {
    if (typeof predicate !== 'function') {
        throw new TypeError('predicate must be a function');
    }

    return records.filter(predicate);
}

function compose(first, second) {
    if (typeof first !== 'function' || typeof second !== 'function') {
        throw new TypeError('compose requires two functions');
    }

    return value => second(first(value));
}

// The closure captures factor after makeMultiplier returns. Each generated
// function retains its own factor without exposing mutable global state.
function makeMultiplier(factor) {
    if (!Number.isFinite(factor)) {
        throw new TypeError('factor must be finite');
    }

    return value => value * factor;
}

// Recursion is useful for tree-shaped data because each child is another
// instance of the same structural problem.
function factorial(n) {
    if (!Number.isInteger(n) || n < 0) {
        throw new RangeError('n must be a non-negative integer');
    }

    if (n <= 1) {
        return 1;
    }

    return n * factorial(n - 1);
}

function* walkTree(tree, prefix = '') {
    for (const [name, children] of Object.entries(tree)) {
        const path = prefix ? `${prefix}/${name}` : name;

        if (children === null) {
            yield path;
        } else {
            yield* walkTree(children, path);
        }
    }
}

function memoize(functionToCache) {
    const cache = new Map();

    return function memoized(...args) {
        const key = JSON.stringify(args);

        if (cache.has(key)) {
            return cache.get(key);
        }

        const result = functionToCache(...args);
        cache.set(key, result);
        return result;
    };
}

const fibonacci = memoize(function fib(n) {
    if (!Number.isInteger(n) || n < 0) {
        throw new RangeError('n must be a non-negative integer');
    }

    if (n < 2) {
        return n;
    }

    return fib(n - 1) + fib(n - 2);
});

class PullRequest {
    constructor(number, sourceBranch, targetBranch) {
        if (!Number.isInteger(number) || number <= 0) {
            throw new RangeError('pull request number must be positive');
        }

        this.number = number;
        this.sourceBranch = sourceBranch;
        this.targetBranch = targetBranch;
        this.state = 'draft';
        this.commits = [];
        this.reviewers = new Set();
        this.approvals = new Set();
        this.statusChecks = new Map();
        this.conflict = false;
    }

    addCommit(sha) {
        if (this.state === 'merged' || this.state === 'closed') {
            throw new Error('cannot add commits to a closed or merged pull request');
        }

        if (!/^[a-f0-9]{7,40}$/.test(sha)) {
            throw new Error('invalid commit identifier');
        }

        this.commits.push(sha);
    }

    markReady() {
        if (this.commits.length === 0) {
            throw new Error('a pull request requires at least one commit');
        }

        this.state = 'open';
    }

    requestReview(reviewer) {
        if (this.state !== 'open') {
            throw new Error('reviews can only be requested on an open pull request');
        }

        this.reviewers.add(reviewer);
    }

    approve(reviewer) {
        if (!this.reviewers.has(reviewer)) {
            throw new Error(`${reviewer} is not an assigned reviewer`);
        }

        this.approvals.add(reviewer);
    }

    setStatusCheck(name, passed) {
        this.statusChecks.set(name, Boolean(passed));
    }

    isMergeable(requiredApprovals) {
        if (this.state !== 'open') return false;
        if (this.commits.length === 0) return false;
        if (this.conflict) return false;
        if (this.approvals.size < requiredApprovals) return false;

        return [...this.statusChecks.values()].every(Boolean);
    }
}

// EventEmitter models the event-driven nature of Node.js workflows.
// Consumers subscribe to events without coupling themselves to the code
// that causes those events.
class PullRequestWorkflow extends EventEmitter {
    open(pullRequest) {
        pullRequest.markReady();
        this.emit('opened', pullRequest);
    }

    synchronize(pullRequest, commit) {
        pullRequest.addCommit(commit);
        this.emit('synchronized', pullRequest);
    }

    merge(pullRequest, requiredApprovals) {
        if (!pullRequest.isMergeable(requiredApprovals)) {
            throw new Error(`PR #${pullRequest.number} is not mergeable`);
        }

        pullRequest.state = 'merged';
        this.emit('merged', pullRequest);
    }
}

function simulateAsyncStatusCheck(name, passed, delay = 25) {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            if (typeof passed !== 'boolean') {
                reject(new TypeError(`status result for ${name} must be boolean`));
                return;
            }

            resolve({ name, passed });
        }, delay);
    });
}

async function runStatusChecks(pullRequest) {
    const checks = await Promise.all([
        simulateAsyncStatusCheck('unit-tests', true),
        simulateAsyncStatusCheck('lint', true),
        simulateAsyncStatusCheck('security-scan', true)
    ]);

    for (const check of checks) {
        pullRequest.setStatusCheck(check.name, check.passed);
    }

    return checks;
}

function demonstrateCoreFunctions() {
    section('Parameters and Return Values');

    console.log('Discount:', calculateDiscount(2000, 10));
    console.log('Final price:', finalPrice(2000, 10));
    console.log('Repository:', parseRepositoryName('  Governance_Engine '));
    console.log('Average:', average([12, 18, 25, 31]));

    section('Higher-Order Functions and Closures');

    const values = [2, 4, 6, 8];

    console.log(
        'Squares:',
        mapRecords(values, value => value ** 2)
    );

    console.log(
        'Values above five:',
        filterRecords(values, value => value > 5)
    );

    const cleanName = compose(
        value => value.trim(),
        value => value.toLowerCase()
    );

    console.log('Composed result:', cleanName('  REVIEW-ENGINE  '));

    const triple = makeMultiplier(3);
    console.log('Closure result:', triple(14));
}

function demonstrateRecursion() {
    section('Recursion and Generators');

    console.log('factorial(7):', factorial(7));
    console.log('fibonacci(35):', fibonacci(35));

    const tree = {
        src: {
            policy: {
                approvals: null,
                checks: null
            },
            workflow: null
        },
        tests: {
            governance: null
        }
    };

    console.log('Repository paths:');
    for (const path of walkTree(tree)) {
        console.log(`  ${path}`);
    }
}

async function demonstrateWorkflow() {
    section('Event-Driven Pull Request Workflow');

    const workflow = new PullRequestWorkflow();

    workflow.on('opened', pr => {
        console.log(`PR #${pr.number} opened: ${pr.sourceBranch} -> ${pr.targetBranch}`);
    });

    workflow.on('synchronized', pr => {
        console.log(`PR #${pr.number} synchronized; commits=${pr.commits.length}`);
    });

    workflow.on('merged', pr => {
        console.log(`PR #${pr.number} merged`);
    });

    const pullRequest = new PullRequest(
        248,
        'feature/review-policy',
        'main'
    );

    workflow.open(pullRequest);
    workflow.synchronize(pullRequest, 'a1b2c3d');
    workflow.synchronize(pullRequest, 'e4f5a6b');

    pullRequest.requestReview('alice');
    pullRequest.requestReview('bob');

    pullRequest.approve('alice');
    pullRequest.approve('bob');

    await runStatusChecks(pullRequest);

    console.log(
        'Merge eligibility:',
        pullRequest.isMergeable(2)
    );

    workflow.merge(pullRequest, 2);
}

async function demonstrateFailureHandling() {
    section('Validation and Failure Handling');

    try {
        calculateDiscount(100, 150);
    } catch (error) {
        console.log('Expected validation failure:', error.message);
    }

    try {
        const pr = new PullRequest(249, 'feature/a', 'main');
        pr.markReady();
    } catch (error) {
        console.log('Expected workflow failure:', error.message);
    }

    try {
        await simulateAsyncStatusCheck('broken-check', 'yes');
    } catch (error) {
        console.log('Expected asynchronous failure:', error.message);
    }
}

async function run() {
    demonstrateCoreFunctions();
    demonstrateRecursion();
    await demonstrateWorkflow();
    await demonstrateFailureHandling();

    section('Executable Assertions');

    assert.equal(factorial(5), 120);
    assert.equal(average([10, 20]), 15);
    assert.equal(makeMultiplier(4)(5), 20);

    console.log('All executable assertions passed.');
}

run().catch(error => {
    console.error('Fatal workflow error:', error);
    process.exitCode = 1;
});
