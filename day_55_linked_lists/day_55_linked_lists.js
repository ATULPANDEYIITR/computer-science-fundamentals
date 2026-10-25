"use strict";

/*
 * Linked-list engineering model:
 * - Singly linked list: one-way traversal.
 * - Doubly linked list: forward and backward traversal.
 * - Circular linked list: tail points back to head.
 *
 * The implementation deliberately uses explicit node objects instead of
 * JavaScript arrays so that pointer relationships remain visible.
 */

class LinkedListError extends Error {}
class IndexOutOfBoundsError extends LinkedListError {}

class SinglyNode {
    constructor(value) {
        this.value = value;
        this.next = null;
    }
}

class SinglyLinkedList {
    constructor(values = []) {
        this.head = null;
        this.tail = null;
        this.size = 0;

        for (const value of values) {
            this.append(value);
        }
    }

    append(value) {
        const node = new SinglyNode(value);

        if (this.head === null) {
            this.head = this.tail = node;
        } else {
            this.tail.next = node;
            this.tail = node;
        }

        this.size++;
    }

    prepend(value) {
        const node = new SinglyNode(value);
        node.next = this.head;
        this.head = node;

        if (this.tail === null) {
            this.tail = node;
        }

        this.size++;
    }

    nodeAt(index) {
        this.validateIndex(index);

        let current = this.head;
        for (let i = 0; i < index; i++) {
            current = current.next;
        }

        return current;
    }

    validateIndex(index, allowEnd = false) {
        const maximum = allowEnd ? this.size : this.size - 1;

        if (!Number.isInteger(index) || index < 0 || index > maximum) {
            throw new IndexOutOfBoundsError(`Invalid index: ${index}`);
        }
    }

    insert(index, value) {
        this.validateIndex(index, true);

        if (index === 0) {
            this.prepend(value);
            return;
        }

        if (index === this.size) {
            this.append(value);
            return;
        }

        const previous = this.nodeAt(index - 1);
        const node = new SinglyNode(value);

        node.next = previous.next;
        previous.next = node;
        this.size++;
    }

    remove(index) {
        this.validateIndex(index);

        if (index === 0) {
            const removed = this.head;
            this.head = removed.next;
            this.size--;

            if (this.size === 0) {
                this.tail = null;
            }

            return removed.value;
        }

        const previous = this.nodeAt(index - 1);
        const removed = previous.next;

        previous.next = removed.next;

        if (removed === this.tail) {
            this.tail = previous;
        }

        this.size--;
        return removed.value;
    }

    reverse() {
        let previous = null;
        let current = this.head;

        this.tail = this.head;

        while (current !== null) {
            const next = current.next;
            current.next = previous;
            previous = current;
            current = next;
        }

        this.head = previous;
    }

    find(value) {
        let current = this.head;
        let index = 0;

        while (current !== null) {
            if (Object.is(current.value, value)) {
                return index;
            }

            current = current.next;
            index++;
        }

        return -1;
    }

    toArray() {
        const result = [];
        let current = this.head;

        while (current !== null) {
            result.push(current.value);
            current = current.next;
        }

        return result;
    }
}

class DoublyNode {
    constructor(value) {
        this.value = value;
        this.previous = null;
        this.next = null;
    }
}

class DoublyLinkedList {
    constructor(values = []) {
        this.head = null;
        this.tail = null;
        this.size = 0;

        for (const value of values) {
            this.append(value);
        }
    }

    append(value) {
        const node = new DoublyNode(value);

        if (this.tail === null) {
            this.head = this.tail = node;
        } else {
            node.previous = this.tail;
            this.tail.next = node;
            this.tail = node;
        }

        this.size++;
    }

    prepend(value) {
        const node = new DoublyNode(value);

        if (this.head === null) {
            this.head = this.tail = node;
        } else {
            node.next = this.head;
            this.head.previous = node;
            this.head = node;
        }

        this.size++;
    }

    nodeAt(index) {
        if (!Number.isInteger(index) || index < 0 || index >= this.size) {
            throw new IndexOutOfBoundsError(`Invalid index: ${index}`);
        }

        if (index <= this.size / 2) {
            let current = this.head;

            for (let i = 0; i < index; i++) {
                current = current.next;
            }

            return current;
        }

        let current = this.tail;

        for (let i = this.size - 1; i > index; i--) {
            current = current.previous;
        }

        return current;
    }

    insert(index, value) {
        if (!Number.isInteger(index) || index < 0 || index > this.size) {
            throw new IndexOutOfBoundsError(`Invalid index: ${index}`);
        }

        if (index === 0) {
            this.prepend(value);
            return;
        }

        if (index === this.size) {
            this.append(value);
            return;
        }

        const target = this.nodeAt(index);
        const node = new DoublyNode(value);

        node.previous = target.previous;
        node.next = target;

        target.previous.next = node;
        target.previous = node;

        this.size++;
    }

    remove(index) {
        const target = this.nodeAt(index);

        if (target.previous === null) {
            this.head = target.next;
        } else {
            target.previous.next = target.next;
        }

        if (target.next === null) {
            this.tail = target.previous;
        } else {
            target.next.previous = target.previous;
        }

        this.size--;
        return target.value;
    }

    reverse() {
        let current = this.head;

        while (current !== null) {
            [current.previous, current.next] = [current.next, current.previous];
            current = current.previous;
        }

        [this.head, this.tail] = [this.tail, this.head];
    }

    forward() {
        const result = [];
        let current = this.head;

        while (current !== null) {
            result.push(current.value);
            current = current.next;
        }

        return result;
    }

    backward() {
        const result = [];
        let current = this.tail;

        while (current !== null) {
            result.push(current.value);
            current = current.previous;
        }

        return result;
    }
}

class CircularLinkedList {
    constructor(values = []) {
        this.head = null;
        this.tail = null;
        this.size = 0;

        for (const value of values) {
            this.append(value);
        }
    }

    append(value) {
        const node = new SinglyNode(value);

        if (this.head === null) {
            this.head = this.tail = node;
            node.next = node;
        } else {
            node.next = this.head;
            this.tail.next = node;
            this.tail = node;
        }

        this.size++;
    }

    nodeAt(index) {
        if (!Number.isInteger(index) || index < 0 || index >= this.size) {
            throw new IndexOutOfBoundsError(`Invalid index: ${index}`);
        }

        let current = this.head;

        for (let i = 0; i < index; i++) {
            current = current.next;
        }

        return current;
    }

    remove(index) {
        if (!Number.isInteger(index) || index < 0 || index >= this.size) {
            throw new IndexOutOfBoundsError(`Invalid index: ${index}`);
        }

        if (this.size === 1) {
            const value = this.head.value;
            this.head = this.tail = null;
            this.size = 0;
            return value;
        }

        if (index === 0) {
            const value = this.head.value;
            this.head = this.head.next;
            this.tail.next = this.head;
            this.size--;
            return value;
        }

        const previous = this.nodeAt(index - 1);
        const removed = previous.next;

        previous.next = removed.next;

        if (removed === this.tail) {
            this.tail = previous;
        }

        this.size--;
        return removed.value;
    }

    rotate(steps) {
        if (this.size === 0) {
            return;
        }

        const normalized = ((steps % this.size) + this.size) % this.size;

        for (let i = 0; i < normalized; i++) {
            this.head = this.head.next;
            this.tail = this.tail.next;
        }
    }

    toArray() {
        const result = [];

        if (this.head === null) {
            return result;
        }

        let current = this.head;

        for (let i = 0; i < this.size; i++) {
            result.push(current.value);
            current = current.next;
        }

        return result;
    }
}

function detectCycle(head) {
    let slow = head;
    let fast = head;

    while (fast !== null && fast.next !== null) {
        slow = slow.next;
        fast = fast.next.next;

        if (slow === fast) {
            return true;
        }
    }

    return false;
}

function mergeSorted(first, second) {
    const result = new SinglyLinkedList();
    let left = first.head;
    let right = second.head;

    while (left !== null && right !== null) {
        if (left.value <= right.value) {
            result.append(left.value);
            left = left.next;
        } else {
            result.append(right.value);
            right = right.next;
        }
    }

    while (left !== null) {
        result.append(left.value);
        left = left.next;
    }

    while (right !== null) {
        result.append(right.value);
        right = right.next;
    }

    return result;
}

function assert(condition, message) {
    if (!condition) {
        throw new Error(`Integrity failure: ${message}`);
    }
}

function validateCircular(list) {
    if (list.size === 0) {
        assert(list.head === null && list.tail === null, "empty circular list");
        return;
    }

    assert(list.tail.next === list.head, "tail must point to head");

    let current = list.head;
    for (let i = 0; i < list.size; i++) {
        current = current.next;
    }

    assert(current === list.head, "cycle must return to head");
}

function runWorkflow() {
    const singly = new SinglyLinkedList([10, 20, 30]);
    singly.prepend(5);
    singly.insert(2, 15);

    console.log("Singly:", singly.toArray());
    console.log("Removed:", singly.remove(1));

    singly.reverse();
    console.log("Reversed singly:", singly.toArray());
    console.log("Cycle detected:", detectCycle(singly.head));

    const first = new SinglyLinkedList([1, 3, 5, 7]);
    const second = new SinglyLinkedList([2, 4, 6, 8]);
    console.log("Merged:", mergeSorted(first, second).toArray());

    const doubly = new DoublyLinkedList(["A", "B", "C", "D"]);
    doubly.insert(2, "X");
    console.log("Doubly forward:", doubly.forward());
    console.log("Doubly backward:", doubly.backward());

    doubly.remove(2);
    doubly.reverse();
    console.log("Doubly reversed:", doubly.forward());

    const circular = new CircularLinkedList([100, 200, 300, 400]);
    circular.rotate(2);
    console.log("Circular:", circular.toArray());
    console.log("Circular removed:", circular.remove(1));
    console.log("Circular after removal:", circular.toArray());

    validateCircular(circular);

    try {
        singly.nodeAt(999);
    } catch (error) {
        console.log("Expected validation failure:", error.message);
    }

    console.log("All linked-list workflows completed successfully.");
}

runWorkflow();
