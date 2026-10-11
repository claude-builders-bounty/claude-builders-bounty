import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedGoldenEagleOptimizerTSPOptimizer } from "./index.ts";

describe("DistributedGoldenEagleOptimizerTSPOptimizer Aquila Chrysaetos Metaheuristic", () => {
    it("simulates golden eagle thermal soaring, spiral diving, and stoop attack, optimizing unit square perimeter", () => {
        const geo = new DistributedGoldenEagleOptimizerTSPOptimizer();

        // 4 square corners: (0,0), (0,1), (1,1), (1,0)
        geo.addPoint("A", 0, 0);
        geo.addPoint("B", 0, 1);
        geo.addPoint("C", 1, 1);
        geo.addPoint("D", 1, 0);

        const result = geo.search(120, 20);
        assert.equal(result.found, true);
        assert.equal(result.tour.length, 5);
        assert.equal(result.tour[0], result.tour[result.tour.length - 1]);

        // Optimal perimeter of square is 4.0
        assert.equal(Math.abs(result.bestCost - 4.0) < 1e-6, true);
        assert.equal(result.bestCost <= result.initialCost, true);
    });

    it("handles single and two point graphs correctly", () => {
        const single = new DistributedGoldenEagleOptimizerTSPOptimizer();
        single.addPoint("P1", 5, 5);
        const resSingle = single.search();
        assert.equal(resSingle.found, true);
        assert.equal(resSingle.bestCost, 0);
        assert.equal(resSingle.tour.length, 2);

        const pair = new DistributedGoldenEagleOptimizerTSPOptimizer();
        pair.addPoint("P1", 0, 0);
        pair.addPoint("P2", 3, 4);
        const resPair = pair.search();
        assert.equal(resPair.found, true);
        assert.equal(resPair.bestCost, 10);
        assert.equal(resPair.tour.length, 3);
    });

    it("defensively handles empty graph and duplicate points", () => {
        const empty = new DistributedGoldenEagleOptimizerTSPOptimizer();
        assert.equal(empty.search().found, false);

        const dup = new DistributedGoldenEagleOptimizerTSPOptimizer();
        dup.addPoint("X", 0, 0);
        dup.addPoint("X", 5, 5);
        assert.equal(dup.search().tour.length, 2);
    });
});
