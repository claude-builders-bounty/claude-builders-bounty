import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedHopcroftKarp } from "./index.js";

describe("DistributedHopcroftKarp Maximum Bipartite Matching", () => {
    it("computes maximum cardinality bipartite matching in O(E sqrt(V))", () => {
        const hk = new DistributedHopcroftKarp();

        // Tasks -> Workers matching
        hk.addEdge("worker_1", "task_A");
        hk.addEdge("worker_1", "task_B");
        hk.addEdge("worker_2", "task_A");
        hk.addEdge("worker_3", "task_B");
        hk.addEdge("worker_3", "task_C");

        const result = hk.computeMaximumMatching();
        assert.equal(result.matchingSize, 3);
        assert.equal(result.pairs.length, 3);
        assert.equal(result.leftMatched.has("worker_1"), true);
        assert.equal(result.leftMatched.has("worker_2"), true);
        assert.equal(result.leftMatched.has("worker_3"), true);
    });

    it("handles disjoint and bottleneck bipartite graphs", () => {
        const hk = new DistributedHopcroftKarp();

        // Bottleneck: 3 left workers only have 1 right task
        hk.addEdge("L1", "R1");
        hk.addEdge("L2", "R1");
        hk.addEdge("L3", "R1");
        // Separate component
        hk.addEdge("L4", "R2");

        const result = hk.computeMaximumMatching();
        assert.equal(result.matchingSize, 2);
        assert.equal(result.rightMatched.get("R2"), "L4");
    });

    it("defensively handles empty graphs and invalid inputs", () => {
        const hk = new DistributedHopcroftKarp();

        hk.addEdge("", "task_1");
        hk.addEdge("worker_1", "");
        hk.addEdge(null as any, "task_2");

        const result = hk.computeMaximumMatching();
        assert.equal(result.matchingSize, 0);
        assert.deepEqual(result.pairs, []);
    });
});