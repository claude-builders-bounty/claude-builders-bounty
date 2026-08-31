import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedVariableNeighborhoodSearchTSP } from "./index.js";

describe("DistributedVariableNeighborhoodSearchTSP Optimization", () => {
    it("untangles crossed tour on unit square with systematic shaking and converges to optimal perimeter", () => {
        const vns = new DistributedVariableNeighborhoodSearchTSP();

        // 4 square corners in crossed order: (0,0), (1,1), (0,1), (1,0)
        vns.addPoint("A", 0, 0);
        vns.addPoint("B", 1, 1);
        vns.addPoint("C", 0, 1);
        vns.addPoint("D", 1, 0);

        const result = vns.search(30, 3);
        assert.equal(result.found, true);
        assert.equal(result.tour.length, 5);
        assert.equal(result.tour[0], result.tour[result.tour.length - 1]);

        // Optimal perimeter of square is 4.0
        assert.equal(Math.abs(result.bestCost - 4.0) < 1e-6, true);
        assert.equal(result.bestCost <= result.initialCost, true);
    });

    it("handles single and two point graphs correctly", () => {
        const single = new DistributedVariableNeighborhoodSearchTSP();
        single.addPoint("P1", 5, 5);
        const resSingle = single.search();
        assert.equal(resSingle.found, true);
        assert.equal(resSingle.bestCost, 0);

        const pair = new DistributedVariableNeighborhoodSearchTSP();
        pair.addPoint("P1", 0, 0);
        pair.addPoint("P2", 3, 4);
        const resPair = pair.search();
        assert.equal(resPair.found, true);
        assert.equal(resPair.bestCost, 10);
    });

    it("defensively handles empty graph and duplicate points", () => {
        const empty = new DistributedVariableNeighborhoodSearchTSP();
        assert.equal(empty.search().found, false);

        const dup = new DistributedVariableNeighborhoodSearchTSP();
        dup.addPoint("X", 0, 0);
        dup.addPoint("X", 5, 5);
        assert.equal(dup.search().tour.length, 2);
    });
});