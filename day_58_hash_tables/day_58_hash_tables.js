'use strict';

/*
 * Hash-table implementation using two collision strategies:
 * 1. Separate chaining with Map-backed buckets.
 * 2. Linear probing with explicit EMPTY/OCCUPIED/DELETED states.
 *
 * The asynchronous policy evaluator at the end models how a hash table
 * can support fast repository-keyed policy lookup without making the
 * hash table itself responsible for application policy.
 */

class HashTableError extends Error {}

class DuplicateKeyError extends HashTableError {}

class KeyNotFoundError extends HashTableError {}

class ChainedHashTable {
    constructor(capacity = 8, maxLoadFactor = 0.75) {
        if (!Number.isInteger(capacity) || capacity < 2) {
            throw new RangeError('capacity must be an integer >= 2');
        }
        if (maxLoadFactor <= 0.1 || maxLoadFactor > 0.95) {
            throw new RangeError('invalid maximum load factor');
        }

        this.buckets = Array.from({ length: capacity }, () => []);
        this.size = 0;
        this.maxLoadFactor = maxLoadFactor;
        this.collisions = 0;
        this.rehashes = 0;
    }

    validateKey(key) {
        const type = typeof key;
        if (
            key === null ||
            (type !== 'string' &&
                type !== 'number' &&
                type !== 'bigint' &&
                type !== 'boolean' &&
                type !== 'symbol')
        ) {
            throw new TypeError(
                'This implementation accepts primitive hash keys only'
            );
        }
        if (type === 'number' && !Number.isFinite(key)) {
            throw new TypeError('numeric keys must be finite');
        }
    }

    hash(key) {
        this.validateKey(key);

        const text = `${typeof key}:${String(key)}`;
        let hash = 2166136261;

        for (let i = 0; i < text.length; i++) {
            hash ^= text.charCodeAt(i);
            hash = Math.imul(hash, 16777619);
        }

        return (hash >>> 0) % this.buckets.length;
    }

    resize(newCapacity) {
        const entries = this.entries();

        this.buckets = Array.from({ length: newCapacity }, () => []);
        this.collisions = 0;
        this.rehashes++;

        for (const [key, value] of entries) {
            const index = this.hash(key);
            if (this.buckets[index].length > 0) {
                this.collisions++;
            }
            this.buckets[index].push({ key, value });
        }
    }

    put(key, value) {
        this.validateKey(key);

        const indexBeforeResize = this.hash(key);
        const bucketBeforeResize = this.buckets[indexBeforeResize];

        for (const entry of bucketBeforeResize) {
            if (Object.is(entry.key, key)) {
                entry.value = value;
                return;
            }
        }

        if ((this.size + 1) / this.buckets.length > this.maxLoadFactor) {
            this.resize(this.buckets.length * 2);
        }

        const index = this.hash(key);
        const bucket = this.buckets[index];

        if (bucket.length > 0) {
            this.collisions++;
        }

        bucket.push({ key, value });
        this.size++;
    }

    add(key, value) {
        if (this.has(key)) {
            throw new DuplicateKeyError(`key already exists: ${String(key)}`);
        }
        this.put(key, value);
    }

    get(key, defaultValue = undefined) {
        const bucket = this.buckets[this.hash(key)];

        for (const entry of bucket) {
            if (Object.is(entry.key, key)) {
                return entry.value;
            }
        }

        return defaultValue;
    }

    require(key) {
        const value = this.get(key);

        if (value === undefined) {
            throw new KeyNotFoundError(`key not found: ${String(key)}`);
        }

        return value;
    }

    has(key) {
        const bucket = this.buckets[this.hash(key)];

        return bucket.some(entry => Object.is(entry.key, key));
    }

    remove(key) {
        const index = this.hash(key);
        const bucket = this.buckets[index];

        const position = bucket.findIndex(entry => Object.is(entry.key, key));

        if (position === -1) {
            throw new KeyNotFoundError(`key not found: ${String(key)}`);
        }

        const [removed] = bucket.splice(position, 1);
        this.size--;
        return removed.value;
    }

    entries() {
        return this.buckets.flatMap(bucket =>
            bucket.map(entry => [entry.key, entry.value])
        );
    }

    get loadFactor() {
        return this.size / this.buckets.length;
    }

    report() {
        const distribution = this.buckets.map(bucket => bucket.length);

        return {
            size: this.size,
            capacity: this.buckets.length,
            loadFactor: Number(this.loadFactor.toFixed(3)),
            collisions: this.collisions,
            rehashes: this.rehashes,
            longestChain: Math.max(...distribution, 0),
            distribution
        };
    }
}


const EMPTY = Symbol('EMPTY');
const DELETED = Symbol('DELETED');


class LinearProbingHashTable {
    constructor(capacity = 11, maxLoadFactor = 0.65) {
        if (!Number.isInteger(capacity) || capacity < 3) {
            throw new RangeError('capacity must be an integer >= 3');
        }

        this.keys = Array(capacity).fill(EMPTY);
        this.values = Array(capacity);
        this.maxLoadFactor = maxLoadFactor;
        this.size = 0;
        this.deleted = 0;
        this.probes = 0;
        this.rehashes = 0;
    }

    hash(key) {
        const text = `${typeof key}:${String(key)}`;
        let hash = 0x811c9dc5;

        for (const character of text) {
            hash ^= character.codePointAt(0);
            hash = Math.imul(hash, 0x01000193);
        }

        return (hash >>> 0) % this.keys.length;
    }

    locate(key) {
        const start = this.hash(key);

        for (let offset = 0; offset < this.keys.length; offset++) {
            const index = (start + offset) % this.keys.length;
            this.probes++;

            if (this.keys[index] === EMPTY) {
                return -1;
            }

            if (this.keys[index] !== DELETED &&
                Object.is(this.keys[index], key)) {
                return index;
            }
        }

        return -1;
    }

    insertWithoutResize(key, value) {
        const start = this.hash(key);

        for (let offset = 0; offset < this.keys.length; offset++) {
            const index = (start + offset) % this.keys.length;

            if (
                this.keys[index] === EMPTY ||
                this.keys[index] === DELETED
            ) {
                if (this.keys[index] === DELETED) {
                    this.deleted--;
                }

                this.keys[index] = key;
                this.values[index] = value;
                this.size++;
                return;
            }
        }

        throw new HashTableError('table is full');
    }

    resize(newCapacity) {
        const oldEntries = [];

        for (let i = 0; i < this.keys.length; i++) {
            if (this.keys[i] !== EMPTY && this.keys[i] !== DELETED) {
                oldEntries.push([this.keys[i], this.values[i]]);
            }
        }

        this.keys = Array(newCapacity).fill(EMPTY);
        this.values = Array(newCapacity);
        this.size = 0;
        this.deleted = 0;
        this.rehashes++;

        for (const [key, value] of oldEntries) {
            this.insertWithoutResize(key, value);
        }
    }

    put(key, value) {
        const existing = this.locate(key);

        if (existing !== -1) {
            this.values[existing] = value;
            return;
        }

        if (
            (this.size + this.deleted + 1) / this.keys.length >
            this.maxLoadFactor
        ) {
            this.resize(this.keys.length * 2);
        }

        this.insertWithoutResize(key, value);
    }

    get(key, defaultValue = undefined) {
        const index = this.locate(key);
        return index === -1 ? defaultValue : this.values[index];
    }

    has(key) {
        return this.locate(key) !== -1;
    }

    remove(key) {
        const index = this.locate(key);

        if (index === -1) {
            throw new KeyNotFoundError(`key not found: ${String(key)}`);
        }

        const value = this.values[index];
        this.keys[index] = DELETED;
        this.values[index] = undefined;
        this.size--;
        this.deleted++;

        return value;
    }

    report() {
        return {
            size: this.size,
            capacity: this.keys.length,
            loadFactor: Number((this.size / this.keys.length).toFixed(3)),
            deletedSlots: this.deleted,
            probes: this.probes,
            rehashes: this.rehashes
        };
    }
}


/*
 * Event-driven policy cache.
 *
 * The hash table stores repository policies. Events invalidate or replace
 * cached entries so stale governance decisions are not retained.
 */
class PolicyCache {
    constructor() {
        this.table = new ChainedHashTable();
        this.listeners = new Map();
    }

    on(eventName, listener) {
        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, new Set());
        }

        this.listeners.get(eventName).add(listener);

        return () => this.listeners.get(eventName)?.delete(listener);
    }

    emit(eventName, payload) {
        for (const listener of this.listeners.get(eventName) ?? []) {
            listener(payload);
        }
    }

    set(repositoryId, policy) {
        this.table.put(repositoryId, policy);
        this.emit('policy-updated', { repositoryId, policy });
    }

    invalidate(repositoryId) {
        if (this.table.has(repositoryId)) {
            this.table.remove(repositoryId);
            this.emit('policy-invalidated', { repositoryId });
        }
    }

    async getOrLoad(repositoryId, loader) {
        const cached = this.table.get(repositoryId);

        if (cached !== undefined) {
            return cached;
        }

        const policy = await loader(repositoryId);
        this.set(repositoryId, policy);
        return policy;
    }
}


async function main() {
    const chained = new ChainedHashTable(4, 0.75);

    for (const [id, name] of [
        [101, 'Asha'],
        [102, 'Ravi'],
        [103, 'Meera'],
        [104, 'Karan'],
        [105, 'Nisha']
    ]) {
        chained.put(id, { id, name });
    }

    console.log('Separate chaining');
    console.log(chained.report());
    console.log('User 103:', chained.require(103));

    chained.put(103, { id: 103, name: 'Meera Updated' });
    console.log('Updated:', chained.require(103));

    const probing = new LinearProbingHashTable(7, 0.65);

    for (const [key, value] of [
        ['A', 10],
        ['B', 20],
        ['C', 30],
        ['D', 40]
    ]) {
        probing.put(key, value);
    }

    console.log('\nLinear probing');
    console.log(probing.report());
    console.log('C:', probing.get('C'));

    probing.remove('C');
    probing.put('C', 300);

    console.log('C after deletion and reinsertion:', probing.get('C'));
    console.log(probing.report());

    const cache = new PolicyCache();

    cache.on('policy-updated', event => {
        console.log(`Policy updated for ${event.repositoryId}`);
    });

    cache.on('policy-invalidated', event => {
        console.log(`Policy invalidated for ${event.repositoryId}`);
    });

    const policy = await cache.getOrLoad('repo-42', async id => {
        await new Promise(resolve => setTimeout(resolve, 5));

        return {
            repositoryId: id,
            requiredApprovals: 2,
            requirePassingChecks: true
        };
    });

    console.log('\nLoaded policy:', policy);

    const cachedPolicy = await cache.getOrLoad(
        'repo-42',
        async () => {
            throw new Error('cache loader should not execute');
        }
    );

    console.log('Cached policy:', cachedPolicy);

    cache.invalidate('repo-42');

    try {
        chained.require(999);
    } catch (error) {
        console.log('Expected failure:', error.message);
    }

    try {
        chained.add(101, { id: 101 });
    } catch (error) {
        console.log('Expected duplicate failure:', error.message);
    }

    if (chained.get(101).name !== 'Asha') {
        throw new Error('hash-table assertion failed');
    }

    if (probing.get('C') !== 300) {
        throw new Error('probing assertion failed');
    }

    console.log('\nAssertions passed.');
}


main().catch(error => {
    console.error('Fatal error:', error.message);
    process.exitCode = 1;
});
