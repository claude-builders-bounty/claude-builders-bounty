import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedVectorClock } from "./index.js";

describe("DistributedVectorClock Causality & Conflict Detection", () => {
    it("tracks sequential happens-before causality correctly", () => {
        const nodeA = new DistributedVectorClock("node_A");
        const nodeB = new DistributedVectorClock("node_B");

        nodeA.tick(); // A: {node_A: 1}
        const snapA = nodeA.getSnapshot();

        nodeB.receive(snapA); // B ticks then joins A: {node_A: 1, node_B: 1}
        const snapB = nodeB.getSnapshot();

        assert.equal(DistributedVectorClock.compare(snapA, snapB), "BEFORE");
        assert.equal(DistributedVectorClock.compare(snapB, snapA), "AFTER");
    });

    it("detects concurrent write conflicts when two nodes tick independently", () => {
        const nodeA = new DistributedVectorClock("node_A");
        const nodeB = new DistributedVectorClock("node_B");

        // Both tick independently without synchronization
        nodeA.tick(); // A: {node_A: 1}
        nodeB.tick(); // B: {node_B: 1}

        const relation = DistributedVectorClock.compare(nodeA.getSnapshot(), nodeB.getSnapshot());
        assert.equal(relation, "CONCURRENT"); // Conflict detected
    });

    it("merges multiple clocks into a single upper bound", () => {
        const c1 = { node_1: 5, node_2: 2 };
        const c2 = { node_1: 3, node_2: 7, node_3: 1 };

        const merged = DistributedVectorClock.mergeAll([c1, c2]);
        assert.deepEqual(merged, { node_1: 5, node_2: 7, node_3: 1 });
    });
});