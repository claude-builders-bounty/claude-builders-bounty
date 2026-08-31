import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedBidirectionalDijkstra } from "./index.js";

describe("DistributedBidirectionalDijkstra Meet-in-the-Middle Search", () => {
    it("finds exact shortest path with bidirectional wavefront expansions", () => {
        const dijkstra = new DistributedBidirectionalDijkstra();

        dijkstra.addEdge("S", "A", 4);
        dijkstra.addEdge("S", "B", 2);
        dijkstra.addEdge("A", "C", 5);
        dijkstra.addEdge("B", "A", 1);
        dijkstra.addEdge("B", "D", 8);
        dijkstra.addEdge("A", "D", 2);
        dijkstra.addEdge("D", "T", 3);
        dijkstra.addEdge("C", "T", 6);

        // Path S -> B (2) -> A (1) -> D (2) -> T (3) = 8
        const result = dijkstra.findShortestPath("S", "T");
        assert.equal(result.found, true);
        assert.equal(result.distance, 8);
        assert.deepEqual(result.path, ["S", "B", "A", "D", "T"]);
        assert.equal(result.nodesVisited > 0, true);
    });

    it("returns found: false when no path connects source and target", () => {
        const dijkstra = new DistributedBidirectionalDijkstra();

        dijkstra.addEdge("A", "B", 10);
        dijkstra.addEdge("C", "D", 5);

        const result = dijkstra.findShortestPath("A", "D");
        assert.equal(result.found, false);
        assert.deepEqual(result.path, []);
        assert.equal(result.distance, Number.POSITIVE_INFINITY);
    });

    it("defensively handles source === target and invalid edges", () => {
        const dijkstra = new DistributedBidirectionalDijkstra();

        dijkstra.addEdge("A", "B", -5); // Negative rejected
        dijkstra.addEdge("X", "X", 10); // Self loop rejected

        const same = dijkstra.findShortestPath("A", "A");
        assert.equal(same.found, true);
        assert.equal(same.distance, 0);
        assert.deepEqual(same.path, ["A"]);
    });
});