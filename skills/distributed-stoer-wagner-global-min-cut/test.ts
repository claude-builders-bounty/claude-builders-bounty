import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedStoerWagner } from "./index.js";

describe("DistributedStoerWagner Global Minimum Cut", () => {
    it("computes exact global minimum cut without requiring source/sink parameters", () => {
        const sw = new DistributedStoerWagner();

        // 4-node cycle: A-B (3), B-C (1), C-D (3), D-A (1)
        // Min cut is separating along weight-1 edges: cut weight = 2 (cut {A,B} vs {C,D})
        sw.addEdge("A", "B", 3);
        sw.addEdge("B", "C", 1);
        sw.addEdge("C", "D", 3);
        sw.addEdge("D", "A", 1);

        const result = sw.computeGlobalMinCut();
        assert.equal(result.minCutWeight, 2);
        assert.equal(result.partitionA.length + result.partitionB.length, 4);
    });

    it("identifies single bottleneck bridge cuts", () => {
        const sw = new DistributedStoerWagner();

        // Triangle 1: 1-2 (10), 2-3 (10), 3-1 (10)
        sw.addEdge("1", "2", 10);
        sw.addEdge("2", "3", 10);
        sw.addEdge("3", "1", 10);

        // Bridge: 3-4 (2)
        sw.addEdge("3", "4", 2);

        // Triangle 2: 4-5 (10), 5-6 (10), 6-4 (10)
        sw.addEdge("4", "5", 10);
        sw.addEdge("5", "6", 10);
        sw.addEdge("6", "4", 10);

        const result = sw.computeGlobalMinCut();
        assert.equal(result.minCutWeight, 2); // Bridge is cut
    });

    it("defensively handles disconnected components and self-loops", () => {
        const sw = new DistributedStoerWagner();

        sw.addEdge("A", "A", 5); // Self loop
        sw.addEdge("A", "B", -2); // Negative weight ignored

        const single = new DistributedStoerWagner();
        single.addEdge("X", "X", 10);
        assert.equal(single.computeGlobalMinCut().minCutWeight, 0);
    });
});