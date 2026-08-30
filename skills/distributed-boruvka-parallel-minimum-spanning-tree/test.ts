import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedBoruvkaMST } from "./index.js";

describe("DistributedBoruvkaMST Parallel Minimum Spanning Tree", () => {
    it("computes exact Minimum Spanning Tree across contraction phases in O(E log V) time", () => {
        const boruvka = new DistributedBoruvkaMST();

        // 4 nodes: 0-1 (10), 0-2 (6), 0-3 (5), 1-3 (15), 2-3 (4)
        boruvka.addEdge("0", "1", 10);
        boruvka.addEdge("0", "2", 6);
        boruvka.addEdge("0", "3", 5);
        boruvka.addEdge("1", "3", 15);
        boruvka.addEdge("2", "3", 4);

        const result = boruvka.computeMST();
        assert.equal(result.isConnected, true);
        assert.equal(result.connectedComponentCount, 1);
        assert.equal(result.mstEdges.length, 3);

        // Optimal MST: 2-3 (4), 0-3 (5), 0-1 (10) = 19
        assert.equal(result.totalWeight, 19);
    });

    it("correctly identifies disconnected graph forests", () => {
        const boruvka = new DistributedBoruvkaMST();

        boruvka.addEdge("A", "B", 3);
        boruvka.addEdge("C", "D", 7);

        const result = boruvka.computeMST();
        assert.equal(result.isConnected, false);
        assert.equal(result.connectedComponentCount, 2);
        assert.equal(result.totalWeight, 10);
        assert.equal(result.mstEdges.length, 2);
    });

    it("defensively handles empty graphs and self loops", () => {
        const empty = new DistributedBoruvkaMST();
        assert.equal(empty.computeMST().mstEdges.length, 0);

        const single = new DistributedBoruvkaMST();
        single.addEdge("X", "X", 10); // Self loop rejected
        assert.equal(single.computeMST().connectedComponentCount, 0);
    });
});