import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedHopcroftTarjanBCC } from "./index.js";

describe("DistributedHopcroftTarjanBCC Vulnerabilities & Blocks", () => {
    it("identifies articulation points and bridges separating biconnected components", () => {
        const bcc = new DistributedHopcroftTarjanBCC();

        // Block 1 (Triangle): A - B, B - C, C - A
        bcc.addEdge("A", "B");
        bcc.addEdge("B", "C");
        bcc.addEdge("C", "A");

        // Bridge: C - D
        bcc.addEdge("C", "D");

        // Block 2 (Square): D - E, E - F, F - G, G - D
        bcc.addEdge("D", "E");
        bcc.addEdge("E", "F");
        bcc.addEdge("F", "G");
        bcc.addEdge("G", "D");

        const result = bcc.computeBCC();

        // Articulation points are C and D
        assert.equal(result.articulationPoints.includes("C"), true);
        assert.equal(result.articulationPoints.includes("D"), true);

        // Bridge is C - D
        assert.equal(result.bridges.length, 1);
        const bridge = result.bridges[0];
        assert.equal((bridge.u === "C" && bridge.v === "D") || (bridge.u === "D" && bridge.v === "C"), true);

        // 3 components: Triangle, Bridge edge, Square
        assert.equal(result.biconnectedComponents.length, 3);
        assert.equal(result.isBiconnected, false);
    });

    it("confirms true biconnectivity on simple cycles without articulation points", () => {
        const bcc = new DistributedHopcroftTarjanBCC();

        // 4-cycle: 1 - 2 - 3 - 4 - 1
        bcc.addEdge("1", "2");
        bcc.addEdge("2", "3");
        bcc.addEdge("3", "4");
        bcc.addEdge("4", "1");

        const result = bcc.computeBCC();
        assert.equal(result.articulationPoints.length, 0);
        assert.equal(result.bridges.length, 0);
        assert.equal(result.biconnectedComponents.length, 1);
        assert.equal(result.isBiconnected, true);
    });

    it("defensively handles empty graphs, duplicate edges and self loops", () => {
        const empty = new DistributedHopcroftTarjanBCC();
        assert.equal(empty.computeBCC().biconnectedComponents.length, 0);

        const dup = new DistributedHopcroftTarjanBCC();
        dup.addEdge("X", "Y");
        dup.addEdge("X", "Y"); // Duplicate ignored
        dup.addEdge("X", "X"); // Self loop ignored

        const res = dup.computeBCC();
        assert.equal(res.bridges.length, 1);
        assert.equal(res.biconnectedComponents.length, 1);
    });
});