import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedMantaRayForagingOptimizationTSPOptimizer } from "./index.ts";

describe("DistributedMantaRayForagingOptimizationTSPOptimizer Marine Megafauna Foraging Metaheuristic", () => {
    it("simulates manta ray chain foraging, cyclone vortex and somersault loops, optimizing unit square perimeter", () => {
        const mrfo = new DistributedMantaRayForagingOptimizationTSPOptimizer();

        // 4 square corners: (0,0), (0,1), (1,1), (1,0)
        mrfo.addPoint("A", 0, 0);
        mrfo.addPoint("B", 0, 1);
        mrfo.addPoint("C", 1, 1);
        mrfo.addPoint("D", 1, 0);

        const result = mrfo.search(120, 20);
        assert.equal(result.found, true);
        assert.equal(result.tour.length, 5);
        assert.equal(result.tour[0], result.tour[result.tour.length - 1]);

        // Optimal perimeter of square is 4.0
        assert.equal(Math.abs(result.bestCost - 4.0) < 1e-6, true);
        assert.equal(result.bestCost <= result.initialCost, true);
    });

    it("handles single and two point graphs correctly", () => {
        const single = new DistributedMantaRayForagingOptimizationTSPOptimizer();
        single.addPoint("P1", 5, 5);
        const resSingle = single.search();
        assert.equal(resSingle.found, true);
        assert.equal(resSingle.bestCost, 0);
        assert.equal(resSingle.tour.length, 2);

        const pair = new DistributedMantaRayForagingOptimizationTSPOptimizer();
        pair.addPoint("P1", 0, 0);
        pair.addPoint("P2", 3, 4);
        const resPair = pair.search();
        assert.equal(resPair.found, true);
        assert.equal(resPair.bestCost, 10);
        assert.equal(resPair.tour.length, 3);
    });

    it("defensively handles empty graph and duplicate points", () => {
        const empty = new DistributedMantaRayForagingOptimizationTSPOptimizer();
        assert.equal(empty.search().found, false);

        const dup = new DistributedMantaRayForagingOptimizationTSPOptimizer();
        dup.addPoint("X", 0, 0);
        dup.addPoint("X", 5, 5);
        assert.equal(dup.search().tour.length, 2);
    });
});
