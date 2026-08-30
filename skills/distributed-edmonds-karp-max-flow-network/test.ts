import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedEdmondsKarp } from "./index.js";

describe("DistributedEdmondsKarp Network Flow & Min-Cut", () => {
    it("computes exact maximum s-t flow and validates min-cut cut-set", () => {
        const ek = new DistributedEdmondsKarp();

        // Classic flow network: S -> A (10), S -> B (10), A -> B (2), A -> T (10), B -> T (10)
        ek.addEdge("S", "A", 10);
        ek.addEdge("S", "B", 10);
        ek.addEdge("A", "B", 2);
        ek.addEdge("A", "T", 10);
        ek.addEdge("B", "T", 10);

        const result = ek.computeMaxFlow("S", "T");
        assert.equal(result.maxFlow, 20);
        assert.equal(result.minCutSourceSet.has("S"), true);
        assert.equal(result.minCutSinkSet.has("T"), true);
    });

    it("handles complex multi-pipe pipeline bottleneck networks", () => {
        const ek = new DistributedEdmondsKarp();

        ek.addEdge("src", "u1", 100);
        ek.addEdge("src", "u2", 50);
        ek.addEdge("u1", "v1", 40);
        ek.addEdge("u1", "v2", 60);
        ek.addEdge("u2", "v2", 30);
        ek.addEdge("v1", "snk", 50);
        ek.addEdge("v2", "snk", 70);

        const result = ek.computeMaxFlow("src", "snk");
        // Bottlenecks: v1 receives 40 (<=50 cap to snk), v2 receives 60+30=90 (limited by 70 cap to snk)
        // Max Flow = 40 + 70 = 110
        assert.equal(result.maxFlow, 110);
    });

    it("defensively handles disconnected components and self-loops", () => {
        const ek = new DistributedEdmondsKarp();

        ek.addEdge("A", "A", 10); // Self loop
        ek.addEdge("A", "B", -5); // Negative capacity ignored

        const result = ek.computeMaxFlow("A", "Z");
        assert.equal(result.maxFlow, 0);
        assert.deepEqual(result.edges, []);
    });
});