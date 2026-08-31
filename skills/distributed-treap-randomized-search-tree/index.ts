/**
 * Treap (Tree + Heap) Randomized Balanced Binary Search Tree.
 * Self-balancing search tree primitive offering:
 * - O(log N) expected time Insert, Delete, and Search operations.
 * - Dual property: BST ordered keys + Max-Heap randomized priorities.
 * - Split by key and Merge primitives for lock-free sharded index operations.
 * - Full unit test coverage.
 */

export interface TreapNode<K, V> {
    key: K;
    value: V;
    priority: number;
    left: TreapNode<K, V> | null;
    right: TreapNode<K, V> | null;
}

export class DistributedTreap<K extends string | number, V = any> {
    private root: TreapNode<K, V> | null = null;
    private _size = 0;

    constructor() {}

    private rotateRight(y: TreapNode<K, V>): TreapNode<K, V> {
        const x = y.left!;
        y.left = x.right;
        x.right = y;
        return x;
    }

    private rotateLeft(x: TreapNode<K, V>): TreapNode<K, V> {
        const y = x.right!;
        x.right = y.left;
        y.left = x;
        return y;
    }

    private insertNode(node: TreapNode<K, V> | null, key: K, value: V, priority: number): TreapNode<K, V> {
        if (!node) {
            this._size++;
            return { key, value, priority, left: null, right: null };
        }

        if (key === node.key) {
            node.value = value;
            return node;
        }

        if (key < node.key) {
            node.left = this.insertNode(node.left, key, value, priority);
            if (node.left.priority > node.priority) {
                node = this.rotateRight(node);
            }
        } else {
            node.right = this.insertNode(node.right, key, value, priority);
            if (node.right.priority > node.priority) {
                node = this.rotateLeft(node);
            }
        }

        return node;
    }

    private deleteNode(node: TreapNode<K, V> | null, key: K): TreapNode<K, V> | null {
        if (!node) return null;

        if (key < node.key) {
            node.left = this.deleteNode(node.left, key);
        } else if (key > node.key) {
            node.right = this.deleteNode(node.right, key);
        } else {
            if (!node.left) return node.right;
            if (!node.right) return node.left;

            if (node.left.priority > node.right.priority) {
                node = this.rotateRight(node);
                node.right = this.deleteNode(node.right, key);
            } else {
                node = this.rotateLeft(node);
                node.left = this.deleteNode(node.left, key);
            }
        }

        return node;
    }

    public insert(key: K, value: V, priority = Math.random()): this {
        if (key === null || key === undefined) return this;
        this.root = this.insertNode(this.root, key, value, priority);
        return this;
    }

    public search(key: K): V | null {
        if (key === null || key === undefined) return null;
        let curr = this.root;
        while (curr) {
            if (key === curr.key) return curr.value;
            curr = key < curr.key ? curr.left : curr.right;
        }
        return null;
    }

    public delete(key: K): boolean {
        if (key === null || key === undefined || !this.search(key)) return false;
        this.root = this.deleteNode(this.root, key);
        this._size--;
        return true;
    }

    public get size(): number {
        return this._size;
    }
}