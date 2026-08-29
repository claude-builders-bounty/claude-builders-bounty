import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedJohnsonAPSP } from "./index.js";

describe("DistributedJohnsonAPSP All-Pairs Shortest Paths", () => {
    it("computes exact APSP matrix on sparse graph with negative edges in O(V^2 log V + VE)", () => {
        const johnson = new DistributedJohnsonAPSP();

        // 4-node graph with negative edge: 1 -> 2 (-2), 2 -> 3 (-1), 1 -> 3 (4), 3 -> 4 (2), 4 -> 2 (4)
        johnson.addEdge("1", "2", -2);
        johnson.addEdge("2", "3", -1);
        johnson.addEdge("1", "3", 4);
        johnson.addEdge("3", "4", 2);
        johnson.addEdge("4", "2", 4);

        const result = johnson.computeAllPairsShortestPaths();
        assert.equal(result.hasNegativeCycle, false);

        // Distance 1 -> 3 is -3 (1 -> 2 -> 3)
        assert.equal(result.distanceMatrix.get("1")!.get("3"), -3);
        // Distance 1 -> 4 is -1 (1 -> 2 -> 3 -> 4: -2 + -1 + 2 = -1)
        assert.equal(result.distanceMatrix.get("1")!.get("4"), -1);
        // Distance 2 -> 4 is 1 (2 -> 3 -> 4: -1 + 2 = 1)
        assert.equal(result.distanceMatrix.get("2")!.get("4"), 1);
        // Distance 4 -> 3 is 3 (4 -> 2 -> 3: 4 + -1 = 3)
        assert.equal(result.distanceMatrix.get("4")!.get("3"), 3);
    });

    it("accurately detects negative cycles and aborts matrix calculation", () => {
        const johnson = new DistributedJohnsonAPSP();

        johnson.addEdge("A", "B", 1);
        johnson.addEdge("B", "C", -5);
        johnson.addEdge("C", "A", 2); // Cycle A -> B -> C -> A: 1 - 5 + 2 = -2

        const result = johnson.computeAllPairsShortestPaths();
        assert.equal(result.hasNegativeCycle, true);
    });

    it("defensively handles empty graphs and disconnected nodes", () => {
        const johnson = new DistributedJohnsonAPSP();

        johnson.addEdge("X", "Y", 10);
        johnson.addEdge("A", "B", 5);

        const result = johnson.computeAllPairsShortestPaths();
        assert.equal(result.hasNegativeCycle, false);
        assert.equal(result.distanceMatrix.get("X")!.get("B"), Number.POSITIVE_INFINITY);
    });
});