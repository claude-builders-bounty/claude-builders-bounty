import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedSPFA } from "./index.js";

describe("DistributedSPFA Shortest Path Faster Algorithm", () => {
    it("computes exact shortest paths on graphs with mixed positive and negative edge weights", () => {
        const spfa = new DistributedSPFA();

        spfa.addEdge("A", "B", 4);
        spfa.addEdge("A", "C", 2);
        spfa.addEdge("C", "B", 1);
        spfa.addEdge("B", "D", 2);
        spfa.addEdge("B", "E", 3);
        spfa.addEdge("C", "D", 4);
        spfa.addEdge("C", "E", 5);
        spfa.addEdge("E", "D", -5); // Negative edge E -> D (-5)

        const result = spfa.computeShortestPaths("A");
        assert.equal(result.hasNegativeCycle, false);
        assert.equal(result.distances.get("A"), 0);
        assert.equal(result.distances.get("C"), 2);
        assert.equal(result.distances.get("B"), 3);
        assert.equal(result.distances.get("E"), 6);
        assert.equal(result.distances.get("D"), 1); // A -> C -> B -> E -> D: 2 + 1 + 3 - 5 = 1

        assert.deepEqual(result.shortestPathTo("D"), ["A", "C", "B", "E", "D"]);
    });

    it("accurately detects negative weight cycles", () => {
        const spfa = new DistributedSPFA();

        spfa.addEdge("1", "2", 1);
        spfa.addEdge("2", "3", 2);
        spfa.addEdge("3", "4", 3);
        spfa.addEdge("4", "2", -10); // Negative cycle 2 -> 3 -> 4 -> 2 with total weight -5

        const result = spfa.computeShortestPaths("1");
        assert.equal(result.hasNegativeCycle, true);
        assert.equal(result.shortestPathTo("4"), null);
    });

    it("defensively handles disconnected components and self-loops", () => {
        const spfa = new DistributedSPFA();

        spfa.addEdge("A", "A", 5); // Self loop
        spfa.addEdge("X", "Y", 10);

        const result = spfa.computeShortestPaths("A");
        assert.equal(result.hasNegativeCycle, false);
        assert.equal(result.distances.get("Y"), Number.POSITIVE_INFINITY);
        assert.equal(result.shortestPathTo("Y"), null);
    });
});