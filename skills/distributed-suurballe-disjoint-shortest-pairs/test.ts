import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedSuurballe } from "./index.js";

describe("DistributedSuurballe Disjoint Shortest Path Pairs", () => {
    it("finds two edge-disjoint shortest paths with minimal total weight", () => {
        const suurballe = new DistributedSuurballe();

        suurballe.addEdge("S", "A", 1);
        suurballe.addEdge("S", "B", 2);
        suurballe.addEdge("A", "C", 1);
        suurballe.addEdge("A", "B", 1);
        suurballe.addEdge("B", "D", 2);
        suurballe.addEdge("C", "D", 1);
        suurballe.addEdge("C", "T", 2);
        suurballe.addEdge("D", "T", 1);

        const result = suurballe.findDisjointPaths("S", "T");
        assert.notEqual(result, null);
        assert.equal(result!.path1[0], "S");
        assert.equal(result!.path1[result!.path1.length - 1], "T");
        assert.equal(result!.path2[0], "S");
        assert.equal(result!.path2[result!.path2.length - 1], "T");
        assert.equal(result!.totalWeight > 0, true);
    });

    it("returns null when only one single bottleneck path exists", () => {
        const suurballe = new DistributedSuurballe();

        suurballe.addEdge("S", "A", 1);
        suurballe.addEdge("A", "B", 1);
        suurballe.addEdge("B", "T", 1);

        const result = suurballe.findDisjointPaths("S", "T");
        assert.equal(result, null);
    });

    it("defensively handles disconnected nodes and invalid edges", () => {
        const suurballe = new DistributedSuurballe();

        suurballe.addEdge("A", "A", 1);
        suurballe.addEdge("A", "B", -5);

        assert.equal(suurballe.findDisjointPaths("A", "Z"), null);
    });
});