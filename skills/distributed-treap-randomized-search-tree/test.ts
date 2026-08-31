import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedTreap } from "./index.js";

describe("DistributedTreap Randomized BST & Heap Priority Balancer", () => {
    it("inserts, searches, and updates keys maintaining BST invariant", () => {
        const treap = new DistributedTreap<number, string>();

        treap.insert(50, "Node 50", 0.9);
        treap.insert(30, "Node 30", 0.8);
        treap.insert(70, "Node 70", 0.7);
        treap.insert(20, "Node 20", 0.95); // High priority -> Rotates to root

        assert.equal(treap.size, 4);
        assert.equal(treap.search(50), "Node 50");
        assert.equal(treap.search(20), "Node 20");
        assert.equal(treap.search(999), null);
    });

    it("deletes nodes and restores heap priority structure", () => {
        const treap = new DistributedTreap<string, number>();

        treap.insert("alice", 100);
        treap.insert("bob", 200);
        treap.insert("charlie", 300);

        assert.equal(treap.size, 3);
        assert.equal(treap.delete("bob"), true);
        assert.equal(treap.size, 2);
        assert.equal(treap.search("bob"), null);
        assert.equal(treap.search("alice"), 100);
    });

    it("defensively handles null keys and non-existent deletes", () => {
        const treap = new DistributedTreap();

        assert.equal(treap.search(null as any), null);
        assert.equal(treap.delete("non_existent"), false);
        treap.insert(null as any, "val");
        assert.equal(treap.size, 0);
    });
});