"use strict";

const { EventEmitter } = require("node:events");

class TreeNode {
    constructor(key, value) {
        this.key = key;
        this.value = value;
        this.left = null;
        this.right = null;
        this.height = 1;
    }
}

class IndexBase {
    constructor() {
        this.root = null;
        this.size = 0;
    }

    static validateKey(key) {
        if (!Number.isSafeInteger(key)) {
            throw new TypeError("Keys must be safe JavaScript integers");
        }
    }

    static validateValue(value) {
        if (typeof value !== "string" || value.trim().length === 0) {
            throw new TypeError("Values must be non-empty strings");
        }

        if (value.length > 200) {
            throw new RangeError("Values cannot exceed 200 characters");
        }
    }

    find(key) {
        IndexBase.validateKey(key);

        let current = this.root;

        while (current !== null) {
            if (key === current.key) {
                return current.value;
            }

            current = key < current.key ? current.left : current.right;
        }

        return undefined;
    }

    inorder() {
        const result = [];
        const stack = [];
        let current = this.root;

        while (current !== null || stack.length > 0) {
            while (current !== null) {
                stack.push(current);
                current = current.left;
            }

            current = stack.pop();
            result.push({ key: current.key, value: current.value });
            current = current.right;
        }

        return result;
    }

    rangeQuery(lower, upper) {
        IndexBase.validateKey(lower);
        IndexBase.validateKey(upper);

        if (lower > upper) {
            throw new RangeError("Lower bound cannot exceed upper bound");
        }

        const result = [];
        const stack = [];
        let current = this.root;

        while (current !== null || stack.length > 0) {
            while (current !== null) {
                if (current.key >= lower) {
                    stack.push(current);
                    current = current.left;
                } else {
                    current = current.right;
                }
            }

            if (stack.length === 0) {
                break;
            }

            current = stack.pop();

            if (current.key > upper) {
                break;
            }

            result.push({ key: current.key, value: current.value });
            current = current.right;
        }

        return result;
    }

    kthSmallest(position) {
        if (!Number.isSafeInteger(position) || position < 1 ||
            position > this.size) {
            throw new RangeError("Position is outside the tree");
        }

        const stack = [];
        let current = this.root;
        let visited = 0;

        while (current !== null || stack.length > 0) {
            while (current !== null) {
                stack.push(current);
                current = current.left;
            }

            current = stack.pop();
            visited += 1;

            if (visited === position) {
                return { key: current.key, value: current.value };
            }

            current = current.right;
        }

        throw new Error("Tree size and traversal results are inconsistent");
    }

    height() {
        if (this.root === null) {
            return 0;
        }

        const queue = [{ node: this.root, depth: 1 }];
        let head = 0;
        let maximum = 0;

        // A moving head avoids repeated Array.shift() operations.
        while (head < queue.length) {
            const { node, depth } = queue[head++];
            maximum = Math.max(maximum, depth);

            if (node.left !== null) {
                queue.push({ node: node.left, depth: depth + 1 });
            }

            if (node.right !== null) {
                queue.push({ node: node.right, depth: depth + 1 });
            }
        }

        return maximum;
    }

    validate(balanced = false) {
        const stack = [];

        if (this.root !== null) {
            stack.push({
                node: this.root,
                lower: null,
                upper: null
            });
        }

        const seen = new Set();
        let count = 0;

        while (stack.length > 0) {
            const { node, lower, upper } = stack.pop();

            if (seen.has(node)) {
                return false;
            }

            seen.add(node);

            if (lower !== null && node.key <= lower) {
                return false;
            }

            if (upper !== null && node.key >= upper) {
                return false;
            }

            count += 1;

            if (node.left !== null) {
                stack.push({
                    node: node.left,
                    lower,
                    upper: node.key
                });
            }

            if (node.right !== null) {
                stack.push({
                    node: node.right,
                    lower: node.key,
                    upper
                });
            }
        }

        if (count !== this.size) {
            return false;
        }

        if (balanced && this.root !== null) {
            const heights = new Map();
            const postorder = [{ node: this.root, visited: false }];

            while (postorder.length > 0) {
                const item = postorder.pop();
                const node = item.node;

                if (!item.visited) {
                    postorder.push({ node, visited: true });

                    if (node.right !== null) {
                        postorder.push({
                            node: node.right,
                            visited: false
                        });
                    }

                    if (node.left !== null) {
                        postorder.push({
                            node: node.left,
                            visited: false
                        });
                    }

                    continue;
                }

                const leftHeight = node.left === null
                    ? 0
                    : heights.get(node.left);
                const rightHeight = node.right === null
                    ? 0
                    : heights.get(node.right);

                const expected = 1 + Math.max(leftHeight, rightHeight);

                if (node.height !== expected ||
                    Math.abs(leftHeight - rightHeight) > 1) {
                    return false;
                }

                heights.set(node, expected);
            }
        }

        return true;
    }
}

class BinarySearchTree extends IndexBase {
    insert(key, value) {
        IndexBase.validateKey(key);
        IndexBase.validateValue(value);

        if (this.root === null) {
            this.root = new TreeNode(key, value);
            this.size = 1;
            return true;
        }

        let current = this.root;

        while (true) {
            if (key === current.key) {
                current.value = value;
                return false;
            }

            if (key < current.key) {
                if (current.left === null) {
                    current.left = new TreeNode(key, value);
                    this.size += 1;
                    return true;
                }

                current = current.left;
            } else {
                if (current.right === null) {
                    current.right = new TreeNode(key, value);
                    this.size += 1;
                    return true;
                }

                current = current.right;
            }
        }
    }

    delete(key) {
        IndexBase.validateKey(key);

        let parent = null;
        let current = this.root;

        while (current !== null && current.key !== key) {
            parent = current;
            current = key < current.key ? current.left : current.right;
        }

        if (current === null) {
            return false;
        }

        if (current.left !== null && current.right !== null) {
            let successorParent = current;
            let successor = current.right;

            while (successor.left !== null) {
                successorParent = successor;
                successor = successor.left;
            }

            current.key = successor.key;
            current.value = successor.value;

            if (successorParent === current) {
                successorParent.right = successor.right;
            } else {
                successorParent.left = successor.right;
            }
        } else {
            const replacement = current.left || current.right;

            if (parent === null) {
                this.root = replacement;
            } else if (parent.left === current) {
                parent.left = replacement;
            } else {
                parent.right = replacement;
            }
        }

        this.size -= 1;
        return true;
    }
}

class AvlTree extends IndexBase {
    static nodeHeight(node) {
        return node === null ? 0 : node.height;
    }

    static refresh(node) {
        node.height = 1 + Math.max(
            AvlTree.nodeHeight(node.left),
            AvlTree.nodeHeight(node.right)
        );
    }

    static balanceFactor(node) {
        return AvlTree.nodeHeight(node.left) -
            AvlTree.nodeHeight(node.right);
    }

    static rotateRight(root) {
        const pivot = root.left;

        if (pivot === null) {
            throw new Error("Invalid right rotation");
        }

        root.left = pivot.right;
        pivot.right = root;

        AvlTree.refresh(root);
        AvlTree.refresh(pivot);

        return pivot;
    }

    static rotateLeft(root) {
        const pivot = root.right;

        if (pivot === null) {
            throw new Error("Invalid left rotation");
        }

        root.right = pivot.left;
        pivot.left = root;

        AvlTree.refresh(root);
        AvlTree.refresh(pivot);

        return pivot;
    }

    static rebalance(node) {
        AvlTree.refresh(node);
        const balance = AvlTree.balanceFactor(node);

        if (balance > 1) {
            if (AvlTree.balanceFactor(node.left) < 0) {
                node.left = AvlTree.rotateLeft(node.left);
            }

            return AvlTree.rotateRight(node);
        }

        if (balance < -1) {
            if (AvlTree.balanceFactor(node.right) > 0) {
                node.right = AvlTree.rotateRight(node.right);
            }

            return AvlTree.rotateLeft(node);
        }

        return node;
    }

    static insertNode(node, key, value) {
        if (node === null) {
            return new TreeNode(key, value);
        }

        if (key < node.key) {
            node.left = AvlTree.insertNode(node.left, key, value);
        } else if (key > node.key) {
            node.right = AvlTree.insertNode(node.right, key, value);
        } else {
            node.value = value;
            return node;
        }

        return AvlTree.rebalance(node);
    }

    insert(key, value) {
        IndexBase.validateKey(key);
        IndexBase.validateValue(value);

        const isNew = this.find(key) === undefined;
        this.root = AvlTree.insertNode(this.root, key, value);

        if (isNew) {
            this.size += 1;
        }

        return isNew;
    }

    static minimum(node) {
        while (node.left !== null) {
            node = node.left;
        }

        return node;
    }

    static deleteNode(node, key) {
        if (node === null) {
            return null;
        }

        if (key < node.key) {
            node.left = AvlTree.deleteNode(node.left, key);
        } else if (key > node.key) {
            node.right = AvlTree.deleteNode(node.right, key);
        } else {
            if (node.left === null) {
                return node.right;
            }

            if (node.right === null) {
                return node.left;
            }

            const successor = AvlTree.minimum(node.right);
            node.key = successor.key;
            node.value = successor.value;
            node.right = AvlTree.deleteNode(node.right, successor.key);
        }

        return AvlTree.rebalance(node);
    }

    delete(key) {
        IndexBase.validateKey(key);

        if (this.find(key) === undefined) {
            return false;
        }

        this.root = AvlTree.deleteNode(this.root, key);
        this.size -= 1;

        return true;
    }
}

/**
 * Serializes mutations and emits domain events.
 * A failed write does not permanently poison the write queue.
 */
class TreeIndexService extends EventEmitter {
    constructor(index) {
        super();

        if (!(index instanceof IndexBase)) {
            throw new TypeError("A valid tree index is required");
        }

        this.index = index;
        this.writeQueue = Promise.resolve();
    }

    enqueue(operation) {
        const result = this.writeQueue.then(operation, operation);

        this.writeQueue = result.catch(() => undefined);
        return result;
    }

    async insert(key, value) {
        IndexBase.validateKey(key);
        IndexBase.validateValue(value);

        return this.enqueue(() => {
            const existed = this.index.find(key) !== undefined;
            this.index.insert(key, value);

            const event = Object.freeze({
                type: existed ? "updated" : "inserted",
                key,
                value,
                timestamp: new Date().toISOString()
            });

            this.emit(event.type, event);
            return event;
        });
    }

    async delete(key) {
        IndexBase.validateKey(key);

        return this.enqueue(() => {
            const removedValue = this.index.find(key);

            if (removedValue === undefined) {
                return Object.freeze({
                    type: "not-found",
                    key
                });
            }

            this.index.delete(key);

            const event = Object.freeze({
                type: "deleted",
                key,
                value: removedValue,
                timestamp: new Date().toISOString()
            });

            this.emit("deleted", event);
            return event;
        });
    }

    async search(key) {
        IndexBase.validateKey(key);

        // Wait for all earlier queued writes before reading the index.
        await this.writeQueue;
        return this.index.find(key);
    }

    async report() {
        await this.writeQueue;

        return {
            nodeCount: this.index.size,
            height: this.index.height(),
            orderedRecords: this.index.inorder(),
            valid: this.index.validate(this.index instanceof AvlTree)
        };
    }
}

async function exerciseService(index) {
    const service = new TreeIndexService(index);
    const observedEvents = [];

    for (const eventName of ["inserted", "updated", "deleted"]) {
        service.on(eventName, event => {
            observedEvents.push(event.type);
        });
    }

    const records = [
        [50, "gateway"],
        [30, "database"],
        [70, "monitor"],
        [20, "worker"],
        [40, "cache"],
        [60, "scheduler"],
        [80, "backup"],
        [65, "logger"]
    ];

    // Concurrent callers are processed in a deterministic write order.
    await Promise.all(
        records.map(([key, value]) => service.insert(key, value))
    );

    await service.insert(50, "gateway-updated");

    if (await service.search(50) !== "gateway-updated") {
        throw new Error("Updated value was not found");
    }

    await service.delete(20);  // Leaf.
    await service.delete(60);  // Node with one child.
    await service.delete(70);  // Node with two children.

    const report = await service.report();

    if (!report.valid) {
        throw new Error("Tree invariant validation failed");
    }

    return {
        ...report,
        range35To70: index.rangeQuery(35, 70),
        smallest: index.kthSmallest(1),
        observedEvents
    };
}

async function compareTreeShapes() {
    const unbalanced = new BinarySearchTree();
    const balanced = new AvlTree();

    for (let key = 1; key <= 1000; key += 1) {
        unbalanced.insert(key, `asset-${key}`);
        balanced.insert(key, `asset-${key}`);
    }

    if (!unbalanced.validate() || !balanced.validate(true)) {
        throw new Error("Initial tree validation failed");
    }

    if (unbalanced.height() !== 1000 || balanced.height() > 11) {
        throw new Error("Unexpected tree heights");
    }

    unbalanced.delete(500);
    balanced.delete(500);

    return {
        inputRecords: 1000,
        unbalancedHeight: unbalanced.height(),
        avlHeight: balanced.height(),
        unbalancedValid: unbalanced.validate(),
        avlValid: balanced.validate(true)
    };
}

async function main() {
    const bstWorkload = await exerciseService(new BinarySearchTree());
    const avlWorkload = await exerciseService(new AvlTree());
    const comparison = await compareTreeShapes();

    console.log(JSON.stringify({
        unbalancedBst: bstWorkload,
        avlTree: avlWorkload,
        sortedInsertionComparison: comparison
    }, null, 2));
}

main().catch(error => {
    console.error("Index operation failed:", error.message);
    process.exitCode = 1;
});
