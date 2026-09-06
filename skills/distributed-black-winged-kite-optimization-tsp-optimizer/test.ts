import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedBlackWingedKiteOptimizationTSPOptimizer } from "./index.ts";

describe("DistributedBlackWingedKiteOptimizationTSPOptimizer Elanus Caeruleus Raptor Metaheuristic", () => {
    it("simulates black-winged kite hovering, vertical plunge and wind gust drift, optimizing unit square perimeter", () => {
        const bko = new DistributedBlackWingedKiteOptimizationTSPOptimizer();

        // 4 square corners: (0,0), (0,1), (1,1), (1,0)
        bko.addPoint("A", 0, 0);
        bko.addPoint("B", 0, 1);
        bko.addPoint("C", 1, 1);
        bko.addPoint("D", 1, 0);

        const result = bko.search(120, 20);
        assert.equal(result.found, true);
        assert.equal(result.tour.length, 5);
        assert.equal(result.tour[0], result.tour[result.tour.length - 1]);

        // Optimal perimeter of square is 4.0
        assert.equal(Math.abs(result.bestCost - 4.0) < 1e-6, true);
        assert.equal(result.bestCost <= result.initialCost, true);
    });

    it("handles single and two point graphs correctly", () => {
        const single = new DistributedBlackWingedKiteOptimizationTSPOptimizer();
        single.addPoint("P1", 5, 5);
        const resSingle = single.search();
        assert.equal(resSingle.found, true);
        assert.equal(resSingle.bestCost, 0);
        assert.equal(resSingle.tour.length, 2);

        const pair = new DistributedBlackWingedKiteOptimizationTSPOptimizer();
        pair.addPoint("P1", 0, 0);
        pair.addPoint("P2", 3, 4);
        const resPair = pair.search();
        assert.equal(resPair.found, true);
        assert.equal(resPair.bestCost, 10);
        assert.equal(resPair.tour.length, 3);
    });

    it("defensively handles empty graph and duplicate points", () => {
        const empty = new DistributedBlackWingedKiteOptimizationTSPOptimizer();
        assert.equal(empty.search().found, false);

        const dup = new DistributedBlackWingedKiteOptimizationTSPOptimizer();
        dup.addPoint("X", 0, 0);
        dup.addPoint("X", 5, 5);
        assert.equal(dup.search().tour.length, 2);
    });
});
