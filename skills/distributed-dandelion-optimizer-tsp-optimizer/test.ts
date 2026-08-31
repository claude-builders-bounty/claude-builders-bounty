import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedDandelionOptimizerTSPOptimizer } from "./index.js";

describe("DistributedDandelionOptimizerTSPOptimizer 3-Stage Flight Metaheuristic", () => {
    it("simulates rising, descending, and landing aerodynamic stages, optimizing unit square perimeter", () => {
        const doOpt = new DistributedDandelionOptimizerTSPOptimizer();

        // 4 square corners: (0,0), (0,1), (1,1), (1,0)
        doOpt.addPoint("A", 0, 0);
        doOpt.addPoint("B", 0, 1);
        doOpt.addPoint("C", 1, 1);
        doOpt.addPoint("D", 1, 0);

        const result = doOpt.search(120, 16);
        assert.equal(result.found, true);
        assert.equal(result.tour.length, 5);
        assert.equal(result.tour[0], result.tour[result.tour.length - 1]);

        // Optimal perimeter of square is 4.0
        assert.equal(Math.abs(result.bestCost - 4.0) < 1e-6, true);
        assert.equal(result.bestCost <= result.initialCost, true);
    });

    it("handles single and two point graphs correctly", () => {
        const single = new DistributedDandelionOptimizerTSPOptimizer();
        single.addPoint("P1", 5, 5);
        const resSingle = single.search();
        assert.equal(resSingle.found, true);
        assert.equal(resSingle.bestCost, 0);

        const pair = new DistributedDandelionOptimizerTSPOptimizer();
        pair.addPoint("P1", 0, 0);
        pair.addPoint("P2", 3, 4);
        const resPair = pair.search();
        assert.equal(resPair.found, true);
        assert.equal(resPair.bestCost, 10);
    });

    it("defensively handles empty graph and duplicate points", () => {
        const empty = new DistributedDandelionOptimizerTSPOptimizer();
        assert.equal(empty.search().found, false);

        const dup = new DistributedDandelionOptimizerTSPOptimizer();
        dup.addPoint("X", 0, 0);
        dup.addPoint("X", 5, 5);
        assert.equal(dup.search().tour.length, 2);
    });
});