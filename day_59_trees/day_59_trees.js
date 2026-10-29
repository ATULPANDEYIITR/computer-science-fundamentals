'use strict';

const assert = require('node:assert/strict');

class TreeNode {
    constructor(value, left = null, right = null) {
        if (!Number.isSafeInteger(value)) {
            throw new TypeError('Tree node values must be safe integers.');
        }
        this.value = value;
        this.left = left;
        this.right = right;
    }
}

class BinaryTree {
    constructor(root = null) {
        this.root = root;
    }

    static fromLevelOrder(values) {
        if (!Array.isArray(values)) {
            throw new TypeError('values must be an array.');
        }
        if (values.length === 0 || values[0] === null) {
            return new BinaryTree();
        }

        const root = new TreeNode(values[0]);
        const queue = [root];
        let head = 0;
        let index = 1;

        while (head < queue.length && index < values.length) {
            const node = queue[head++];

            if (index < values.length && values[index] !== null) {
                node.left = new TreeNode(values[index]);
                queue.push(node.left);
            }
            index++;

            if (index < values.length && values[index] !== null) {
                node.right = new TreeNode(values[index]);
                queue.push(node.right);
            }
            index++;
        }

        return new BinaryTree(root);
    }

    preorder() {
        const result = [];
        const stack = this.root ? [this.root] : [];

        while (stack.length) {
            const node = stack.pop();
            result.push(node.value);

            if (node.right) stack.push(node.right);
            if (node.left) stack.push(node.left);
        }

        return result;
    }

    inorder() {
        const result = [];
        const stack = [];
        let current = this.root;

        while (current || stack.length) {
            while (current) {
                stack.push(current);
                current = current.left;
            }

            current = stack.pop();
            result.push(current.value);
            current = current.right;
        }

        return result;
    }

    postorder() {
        if (!this.root) return [];

        const result = [];
        const stack = [[this.root, false]];

        while (stack.length) {
            const [node, expanded] = stack.pop();

            if (expanded) {
                result.push(node.value);
                continue;
            }

            stack.push([node, true]);
            if (node.right) stack.push([node.right, false]);
            if (node.left) stack.push([node.left, false]);
        }

        return result;
    }

    levelOrder() {
        if (!this.root) return [];

        const result = [];
        const queue = [this.root];
        let head = 0;

        while (head < queue.length) {
            const node = queue[head++];
            result.push(node.value);

            if (node.left) queue.push(node.left);
            if (node.right) queue.push(node.right);
        }

        return result;
    }

    height() {
        if (!this.root) return 0;

        const queue = [this.root];
        let head = 0;
        let height = 0;

        while (head < queue.length) {
            const levelEnd = queue.length;
            height++;

            while (head < levelEnd) {
                const node = queue[head++];

                if (node.left) queue.push(node.left);
                if (node.right) queue.push(node.right);
            }
        }

        return height;
    }
}

class BinarySearchTree extends BinaryTree {
    insert(value) {
        if (!Number.isSafeInteger(value)) {
            throw new TypeError('BST keys must be safe integers.');
        }

        if (!this.root) {
            this.root = new TreeNode(value);
            return;
        }

        let current = this.root;

        while (true) {
            if (value === current.value) {
                throw new Error(`Duplicate key: ${value}`);
            }

            if (value < current.value) {
                if (!current.left) {
                    current.left = new TreeNode(value);
                    return;
                }
                current = current.left;
            } else {
                if (!current.right) {
                    current.right = new TreeNode(value);
                    return;
                }
                current = current.right;
            }
        }
    }

    search(value) {
        let current = this.root;

        while (current) {
            if (value === current.value) return true;
            current = value < current.value ? current.left : current.right;
        }

        return false;
    }

    validate() {
        const stack = [{
            node: this.root,
            lower: null,
            upper: null
        }];

        while (stack.length) {
            const { node, lower, upper } = stack.pop();
            if (!node) continue;

            if (lower !== null && node.value <= lower) return false;
            if (upper !== null && node.value >= upper) return false;

            stack.push({
                node: node.left,
                lower,
                upper: node.value
            });

            stack.push({
                node: node.right,
                lower: node.value,
                upper
            });
        }

        return true;
    }

    rangeQuery(min, max) {
        if (!Number.isSafeInteger(min) || !Number.isSafeInteger(max)) {
            throw new TypeError('Range limits must be safe integers.');
        }
        if (min > max) {
            throw new RangeError('Minimum cannot exceed maximum.');
        }

        const result = [];

        const visit = (node) => {
            if (!node) return;

            if (node.value > min) visit(node.left);
            if (node.value >= min && node.value <= max) {
                result.push(node.value);
            }
            if (node.value < max) visit(node.right);
        };

        visit(this.root);
        return result;
    }
}

class TreeEventBus {
    constructor() {
        this.listeners = new Map();
    }

    on(event, listener) {
        if (typeof listener !== 'function') {
            throw new TypeError('Listener must be a function.');
        }

        if (!this.listeners.has(event)) {
            this.listeners.set(event, new Set());
        }

        this.listeners.get(event).add(listener);
        return () => this.listeners.get(event)?.delete(listener);
    }

    emit(event, payload) {
        const listeners = this.listeners.get(event);
        if (!listeners) return;

        for (const listener of listeners) {
            listener(payload);
        }
    }
}

async function processTreeOperations(tree, operations) {
    if (!Array.isArray(operations)) {
        throw new TypeError('operations must be an array.');
    }

    const results = [];

    for (const operation of operations) {
        await Promise.resolve();

        switch (operation.type) {
            case 'insert':
                tree.insert(operation.value);
                results.push(`inserted:${operation.value}`);
                break;

            case 'search':
                results.push({
                    operation: 'search',
                    value: operation.value,
                    found: tree.search(operation.value)
                });
                break;

            case 'range':
                results.push({
                    operation: 'range',
                    values: tree.rangeQuery(operation.min, operation.max)
                });
                break;

            default:
                throw new Error(`Unsupported operation: ${operation.type}`);
        }
    }

    return results;
}

async function main() {
    const tree = new BinarySearchTree();
    const events = new TreeEventBus();

    events.on('inserted', ({ value }) => {
        console.log(`event: inserted ${value}`);
    });

    for (const value of [50, 30, 70, 20, 40, 60, 80, 65]) {
        tree.insert(value);
        events.emit('inserted', { value });
    }

    assert.equal(tree.validate(), true);
    assert.deepEqual(tree.inorder(), [20, 30, 40, 50, 60, 65, 70, 80]);
    assert.equal(tree.search(65), true);
    assert.equal(tree.search(99), false);
    assert.deepEqual(tree.rangeQuery(35, 70), [40, 50, 60, 65, 70]);

    const operations = [
        { type: 'search', value: 65 },
        { type: 'search', value: 99 },
        { type: 'range', min: 20, max: 60 }
    ];

    const results = await processTreeOperations(tree, operations);

    console.log('\nTree traversals');
    console.log('preorder :', tree.preorder());
    console.log('inorder  :', tree.inorder());
    console.log('postorder:', tree.postorder());
    console.log('level    :', tree.levelOrder());
    console.log('height   :', tree.height());
    console.log('valid    :', tree.validate());

    console.log('\nAsynchronous operation results');
    console.dir(results, { depth: null });

    try {
        tree.insert(50);
    } catch (error) {
        console.log('expected failure:', error.message);
    }

    // Security considerations:
    // - Numeric keys are restricted to safe integers to avoid precision errors.
    // - Operations are validated before tree mutation.
    // - No dynamic code execution or external input is evaluated.
    // Performance:
    // - Traversals are O(n).
    // - BST lookup and insertion are O(h).
    // - A skewed BST can degrade to O(n), so production systems may require
    //   a self-balancing tree for predictable lookup performance.
}

main().catch((error) => {
    console.error('Fatal error:', error.message);
    process.exitCode = 1;
});
