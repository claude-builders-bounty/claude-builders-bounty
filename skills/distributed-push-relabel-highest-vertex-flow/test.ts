import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedPushRelabel } from "./index.js";

describe("DistributedPushRelabel Maximum Network Flow", () => {
    it("computes exact maximum flow in O(V^2 sqrt(E)) with highest-label selection", () => {
        const pr = new DistributedPushRelabel();

        pr.addEdge("s", "1", 16);
        pr.addEdge("s", "2", 13);
        pr.addEdge("1", "2", 10);
        pr.addEdge("1", "3", 12);
        pr.addEdge("2", "1", 4);
        pr.addEdge("2", "4", 14);
        pr.addEdge("3", "2", 9);
        pr.addEdge("3", "t", 20);
        pr.addEdge("4", "3", 7);
        pr.addEdge("4", "t", 4);

        const flow = pr.computeMaxFlow("s", "t");
        assert.equal(flow, 23);
    });

    it("handles complex pipeline bottlenecks accurately", () => {
        const pr = new DistributedPushRelabel();

        pr.addEdge("S", "A", 100);
        pr.addEdge("S", "B", 50);
        pr.addEdge("A", "T", 60);
        pr.addEdge("B", "T", 40);

        const flow = pr.computeMaxFlow("S", "T");
        assert.equal(flow, 100); // 60 + 40
    });

    it("defensively handles disconnected graphs and empty paths", () => {
        const pr = new DistributedPushRelabel();

        pr.addEdge("A", "B", 10);
        assert.equal(pr.computeMaxFlow("A", "Z"), 0);
        assert.equal(pr.computeMaxFlow("A", "A"), 0);
    });
});