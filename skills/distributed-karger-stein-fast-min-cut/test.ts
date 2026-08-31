import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedKargerStein } from "./index.js";

describe("DistributedKargerStein Recursive Global Minimum Cut", () => {
    it("finds exact global minimum cut on barbell graph connecting two cliques via a single bridge", () => {
        const ks = new DistributedKargerStein();

        // Clique 1: 1, 2, 3 (all edges weight 5)
        ks.addEdge("1", "2", 5);
        ks.addEdge("2", "3", 5);
        ks.addEdge("3", "1", 5);

        // Bridge: 3 - 4 (weight 1)
        ks.addEdge("3", "4", 1);

        // Clique 2: 4, 5, 6 (all edges weight 5)
        ks.addEdge("4", "5", 5);
        ks.addEdge("5", "6", 5);
        ks.addEdge("6", "4", 5);

        const result = ks.computeGlobalMinCut(15);
        assert.equal(result.minCutWeight, 1);
        assert.equal(result.partitionA.length, 3);
        assert.equal(result.partitionB.length, 3);
    });

    it("identifies minimum cut on 4-cycle", () => {
        const ks = new DistributedKargerStein();

        // Cycle: A-B (2), B-C (10), C-D (2), D-A (10)
        // Min cut cuts A-B and C-D (cut weight = 4)
        ks.addEdge("A", "B", 2);
        ks.addEdge("B", "C", 10);
        ks.addEdge("C", "D", 2);
        ks.addEdge("D", "A", 10);

        const result = ks.computeGlobalMinCut(10);
        assert.equal(result.minCutWeight, 4);
    });

    it("defensively handles single-node graphs and invalid edges", () => {
        const ks = new DistributedKargerStein();

        ks.addEdge("X", "X", 10); // Self loop
        ks.addEdge("X", "Y", -5); // Negative weight rejected

        const single = new DistributedKargerStein();
        single.addEdge("Solo", "Solo", 5);
        const res = single.computeGlobalMinCut();
        assert.equal(res.minCutWeight, 0);
    });
});