import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedDinicMaxFlow } from "./index.js";

describe("DistributedDinicMaxFlow Blocking Flow Algorithm", () => {
    it("computes maximum network flow in O(V^2 E) using level graphs", () => {
        const dinic = new DistributedDinicMaxFlow();

        dinic.addEdge("s", "1", 10);
        dinic.addEdge("s", "2", 10);
        dinic.addEdge("1", "2", 2);
        dinic.addEdge("1", "t", 4);
        dinic.addEdge("1", "3", 8);
        dinic.addEdge("2", "4", 9);
        dinic.addEdge("3", "t", 10);
        dinic.addEdge("4", "3", 6);
        dinic.addEdge("4", "t", 10);

        const flow = dinic.computeMaxFlow("s", "t");
        assert.equal(flow, 19);
    });

    it("handles unit networks and multi-level pipelines", () => {
        const dinic = new DistributedDinicMaxFlow();

        dinic.addEdge("S", "A", 100);
        dinic.addEdge("S", "B", 50);
        dinic.addEdge("A", "T", 70);
        dinic.addEdge("B", "T", 40);

        const flow = dinic.computeMaxFlow("S", "T");
        assert.equal(flow, 110);
    });

    it("defensively handles disconnected graphs and empty paths", () => {
        const dinic = new DistributedDinicMaxFlow();

        dinic.addEdge("A", "B", 10);
        dinic.addEdge("C", "D", 20);

        assert.equal(dinic.computeMaxFlow("A", "D"), 0);
        assert.equal(dinic.computeMaxFlow("A", "A"), 0);
    });
});