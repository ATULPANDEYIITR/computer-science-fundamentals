"use strict";

/*
 * Balanced-tree policy and event model.
 *
 * The AVL implementation maintains an exact height invariant.
 * The Red-Black implementation focuses on insertion balancing and exposes
 * color information useful for understanding the weaker height bound.
 */

class AVLNode {
    constructor(key) {
        this.key = key;
        this.height = 1;
        this.left = null;
        this.right = null;
    }
}

class AVLTree {
    constructor() {
        this.root = null;
    }

    static height(node) {
        return node ? node.height : 0;
    }

    static updateHeight(node) {
        node.height = 1 + Math.max(
            AVLTree.height(node.left),
            AVLTree.height(node.right)
        );
    }

    static balanceFactor(node) {
        return node ? AVLTree.height(node.left) - AVLTree.height(node.right) : 0;
    }

    rotateLeft(x) {
        const y = x.right;
        if (!y) throw new Error("Left rotation requires a right child");

        x.right = y.left;
        y.left = x;

        AVLTree.updateHeight(x);
        AVLTree.updateHeight(y);
        return y;
    }

    rotateRight(y) {
        const x = y.left;
        if (!x) throw new Error("Right rotation requires a left child");

        y.left = x.right;
        x.right = y;

        AVLTree.updateHeight(y);
        AVLTree.updateHeight(x);
        return x;
    }

    insert(key) {
        this.#validateKey(key);
        this.root = this.#insert(this.root, key);
    }

    #insert(node, key) {
        if (!node) return new AVLNode(key);

        if (key < node.key) {
            node.left = this.#insert(node.left, key);
        } else if (key > node.key) {
            node.right = this.#insert(node.right, key);
        } else {
            throw new Error(`Duplicate key: ${key}`);
        }

        AVLTree.updateHeight(node);
        const balance = AVLTree.balanceFactor(node);

        if (balance > 1 && key < node.left.key) {
            return this.rotateRight(node);
        }

        if (balance < -1 && key > node.right.key) {
            return this.rotateLeft(node);
        }

        if (balance > 1 && key > node.left.key) {
            node.left = this.rotateLeft(node.left);
            return this.rotateRight(node);
        }

        if (balance < -1 && key < node.right.key) {
            node.right = this.rotateRight(node.right);
            return this.rotateLeft(node);
        }

        return node;
    }

    delete(key) {
        this.#validateKey(key);
        this.root = this.#delete(this.root, key);
    }

    #delete(node, key) {
        if (!node) return null;

        if (key < node.key) {
            node.left = this.#delete(node.left, key);
        } else if (key > node.key) {
            node.right = this.#delete(node.right, key);
        } else {
            if (!node.left) return node.right;
            if (!node.right) return node.left;

            let successor = node.right;
            while (successor.left) successor = successor.left;
            node.key = successor.key;
            node.right = this.#delete(node.right, successor.key);
        }

        AVLTree.updateHeight(node);
        const balance = AVLTree.balanceFactor(node);

        if (balance > 1 && AVLTree.balanceFactor(node.left) >= 0) {
            return this.rotateRight(node);
        }

        if (balance > 1 && AVLTree.balanceFactor(node.left) < 0) {
            node.left = this.rotateLeft(node.left);
            return this.rotateRight(node);
        }

        if (balance < -1 && AVLTree.balanceFactor(node.right) <= 0) {
            return this.rotateLeft(node);
        }

        if (balance < -1 && AVLTree.balanceFactor(node.right) > 0) {
            node.right = this.rotateRight(node.right);
            return this.rotateLeft(node);
        }

        return node;
    }

    has(key) {
        let node = this.root;
        while (node) {
            if (node.key === key) return true;
            node = key < node.key ? node.left : node.right;
        }
        return false;
    }

    toArray() {
        const values = [];
        const stack = [];
        let node = this.root;

        while (stack.length || node) {
            while (node) {
                stack.push(node);
                node = node.left;
            }
            node = stack.pop();
            values.push(node.key);
            node = node.right;
        }

        return values;
    }

    validate() {
        const check = (node, low, high) => {
            if (!node) return 0;
            if (low !== null && node.key <= low) throw new Error("BST violation");
            if (high !== null && node.key >= high) throw new Error("BST violation");

            const leftHeight = check(node.left, low, node.key);
            const rightHeight = check(node.right, node.key, high);
            const expected = 1 + Math.max(leftHeight, rightHeight);

            if (node.height !== expected) throw new Error("Height violation");
            if (Math.abs(leftHeight - rightHeight) > 1) {
                throw new Error("AVL balance violation");
            }

            return expected;
        };

        return check(this.root, null, null);
    }

    #validateKey(key) {
        if (!Number.isSafeInteger(key)) {
            throw new TypeError("Keys must be safe integers");
        }
    }
}

/*
 * A small asynchronous workload runner models a service that receives
 * batches of keys. Promise scheduling separates request handling from the
 * tree operation while preserving deterministic batch order.
 */
class TreeService {
    constructor() {
        this.tree = new AVLTree();
        this.processed = 0;
    }

    async processBatch(keys) {
        return Promise.resolve().then(() => {
            if (!Array.isArray(keys)) throw new TypeError("Batch must be an array");

            for (const key of keys) {
                this.tree.insert(key);
                this.processed++;
            }

            const height = this.tree.validate();
            return {
                processed: this.processed,
                height,
                values: this.tree.toArray()
            };
        });
    }
}

async function main() {
    const service = new TreeService();

    // Monotonic input is deliberately chosen because an unbalanced BST
    // would degrade toward O(n) height.
    const firstBatch = Array.from({ length: 16 }, (_, i) => i + 1);
    const state = await service.processBatch(firstBatch);

    console.log("AVL state:", state);
    console.log("Contains 8:", service.tree.has(8));
    console.log("Contains 99:", service.tree.has(99));

    service.tree.delete(8);
    service.tree.delete(15);
    service.tree.validate();

    console.log("After deletion:", service.tree.toArray());

    try {
        await service.processBatch([8]);
        await service.processBatch([8]);
    } catch (error) {
        console.log("Expected duplicate-key failure:", error.message);
    }

    try {
        service.tree.insert(Number.MAX_SAFE_INTEGER + 1);
    } catch (error) {
        console.log("Expected key validation failure:", error.message);
    }
}

main().catch(error => {
    console.error("Fatal tree-service error:", error.message);
    process.exitCode = 1;
});
