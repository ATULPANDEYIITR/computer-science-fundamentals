'use strict';

class ArrayOperationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ArrayOperationError';
    }
}

class ObservableArray {
    constructor(values = [], capacity = 4) {
        if (!Number.isInteger(capacity) || capacity <= 0) {
            throw new ArrayOperationError('Capacity must be a positive integer.');
        }

        if (!Array.isArray(values) || !values.every(Number.isInteger)) {
            throw new TypeError('The array must contain integers.');
        }

        this.data = [...values];
        this.capacity = Math.max(capacity, this.data.length);
        this.events = [];
    }

    emit(type, details = {}) {
        const event = {
            type,
            timestamp: new Date().toISOString(),
            ...details
        };
        this.events.push(event);
        return event;
    }

    validateIndex(index, allowEnd = false) {
        const upper = allowEnd ? this.data.length : this.data.length - 1;

        if (!Number.isInteger(index) || index < 0 || index > upper) {
            throw new ArrayOperationError(
                `Invalid index ${index}; valid range is 0..${upper}.`
            );
        }
    }

    ensureCapacity() {
        if (this.data.length >= this.capacity) {
            this.capacity *= 2;
            this.emit('capacity-expanded', { capacity: this.capacity });
        }
    }

    get(index) {
        this.validateIndex(index);
        const value = this.data[index];
        this.emit('access', { index, value });
        return value;
    }

    set(index, value) {
        this.validateIndex(index);

        if (!Number.isInteger(value)) {
            throw new TypeError('Only integers are supported.');
        }

        const previous = this.data[index];
        this.data[index] = value;
        this.emit('update', { index, previous, value });
    }

    append(value) {
        this.insert(this.data.length, value);
    }

    insert(index, value) {
        this.validateIndex(index, true);

        if (!Number.isInteger(value)) {
            throw new TypeError('Only integers are supported.');
        }

        this.ensureCapacity();

        // splice performs the suffix shift required by an indexed insertion.
        this.data.splice(index, 0, value);

        this.emit('insert', { index, value });
    }

    remove(index) {
        this.validateIndex(index);
        const [removed] = this.data.splice(index, 1);

        this.emit('delete', { index, removed });
        return removed;
    }

    linearSearch(value) {
        for (let i = 0; i < this.data.length; i += 1) {
            if (this.data[i] === value) {
                this.emit('linear-search', { value, index: i });
                return i;
            }
        }

        this.emit('linear-search', { value, index: -1 });
        return -1;
    }

    binarySearch(value) {
        for (let i = 1; i < this.data.length; i += 1) {
            if (this.data[i - 1] > this.data[i]) {
                throw new ArrayOperationError(
                    'Binary search requires sorted data.'
                );
            }
        }

        let low = 0;
        let high = this.data.length - 1;

        while (low <= high) {
            const middle = low + Math.floor((high - low) / 2);

            if (this.data[middle] === value) {
                this.emit('binary-search', { value, index: middle });
                return middle;
            }

            if (this.data[middle] < value) {
                low = middle + 1;
            } else {
                high = middle - 1;
            }
        }

        this.emit('binary-search', { value, index: -1 });
        return -1;
    }

    traverse(visitor) {
        if (typeof visitor !== 'function') {
            throw new TypeError('Traversal requires a function.');
        }

        for (let index = 0; index < this.data.length; index += 1) {
            visitor(this.data[index], index);
        }
    }

    reverse() {
        let left = 0;
        let right = this.data.length - 1;

        while (left < right) {
            [this.data[left], this.data[right]] =
                [this.data[right], this.data[left]];
            left += 1;
            right -= 1;
        }

        this.emit('reverse');
    }

    snapshot() {
        return [...this.data];
    }
}

function assert(condition, message) {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}

function runDemo() {
    const values = new ObservableArray([], 2);

    [10, 20, 30, 40].forEach(value => values.append(value));

    assert(values.get(1) === 20, 'indexed access');
    assert(values.linearSearch(30) === 2, 'linear search');
    assert(values.linearSearch(999) === -1, 'missing search');

    values.set(1, 25);
    assert(values.snapshot().join(',') === '10,25,30,40', 'update');

    values.insert(2, 27);
    assert(values.snapshot().join(',') === '10,25,27,30,40', 'insert');

    assert(values.remove(1) === 25, 'delete');
    values.reverse();
    assert(values.snapshot().join(',') === '40,30,27,10', 'reverse');

    const sorted = new ObservableArray([10, 20, 30, 40, 50]);
    assert(sorted.binarySearch(40) === 3, 'binary search');
    assert(sorted.binarySearch(999) === -1, 'binary search miss');

    values.traverse((value, index) => {
        console.log(`index=${index}, value=${value}`);
    });

    console.log('Current array:', values.snapshot());
    console.log('Capacity:', values.capacity);
    console.log('Events:', values.events.length);

    try {
        values.get(100);
    } catch (error) {
        console.log('Invalid access rejected:', error.message);
    }

    try {
        const unsorted = new ObservableArray([30, 10, 20]);
        unsorted.binarySearch(10);
    } catch (error) {
        console.log('Invalid binary search rejected:', error.message);
    }

    console.log('\nComplexity:');
    console.log('Indexed access: O(1)');
    console.log('Linear search: O(n)');
    console.log('Binary search: O(log n) on sorted data');
    console.log('Indexed insertion/deletion: O(n)');
    console.log('Append: amortized O(1)');
    console.log('Traversal: O(n)');
}

runDemo();
