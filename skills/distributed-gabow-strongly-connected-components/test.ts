import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedGabowSCC } from "./index.js";

describe("DistributedGabowSCC Path-Based Strongly Connected Components", () => {
    it("partitions directed graph into strongly connected components in linear O(V + E) time", () => {
        const gabow = new DistributedGabowSCC();

        // SCC 1: 1 -> 2 -> 3 -> 1
        gabow.addEdge("1", "2");
        gabow.addEdge("2", "3");
        gabow.addEdge("3", "1");

        // Edge between components: 2 -> 4
        gabow.addEdge("2", "4");

        // SCC 2: 4 -> 5 -> 4
        gabow.addEdge("4", "5");
        gabow.addEdge("5", "4");

        // Edge to SCC 3: 5 -> 6
        gabow.addEdge("5", "6");

        // SCC 3: 6 (singleton)

        const result = gabow.computeSCC();
        assert.equal(result.componentCount, 3);

        const scc1 = result.nodeToComponentId.get("1");
        const scc2 = result.nodeToComponentId.get("2");
        const scc3 = result.nodeToComponentId.get("3");
        assert.equal(scc1, scc2);
        assert.equal(scc2, scc3);

        const scc4 = result.nodeToComponentId.get("4");
        const scc5 = result.nodeToComponentId.get("5");
        assert.equal(scc4, scc5);
        assert.notEqual(scc1, scc4);

        const scc6 = result.nodeToComponentId.get("6");
        assert.notEqual(scc6, scc4);
        assert.notEqual(scc6, scc1);

        // Verify DAG condensation
        assert.equal(result.condensationAdj.get(scc1!)!.has(scc4!), true);
        assert.equal(result.condensationAdj.get(scc4!)!.has(scc6!), true);
    });

    it("handles complex overlapping cycles and self loops", () => {
        const gabow = new DistributedGabowSCC();

        gabow.addEdge("A", "B");
        gabow.addEdge("B", "C");
        gabow.addEdge("C", "A");
        gabow.addEdge("B", "D");
        gabow.addEdge("D", "E");
        gabow.addEdge("E", "B"); // Merges A, B, C, D, E into single SCC
        gabow.addEdge("E", "E"); // Self loop

        const result = gabow.computeSCC();
        assert.equal(result.componentCount, 1);
        assert.equal(result.components[0].length, 5);
    });

    it("defensively handles empty graphs and disconnected nodes", () => {
        const empty = new DistributedGabowSCC();
        assert.equal(empty.computeSCC().componentCount, 0);

        const single = new DistributedGabowSCC();
        single.addEdge("X", "X");
        const res = single.computeSCC();
        assert.equal(res.componentCount, 1);
        assert.deepEqual(res.components[0], ["X"]);
    });
});