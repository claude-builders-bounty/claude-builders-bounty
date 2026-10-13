import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedRemoraOptimizationAlgorithmTSPOptimizer } from "./index.ts";

describe("DistributedRemoraOptimizationAlgorithmTSPOptimizer Metaheuristic", () => {
    it("simulates remora multi-host hitchhiking, sailfish surging, shark scavenging, and host switching, optimizing unit square perimeter", () => {
        const roa = new DistributedRemoraOptimizationAlgorithmTSPOptimizer();

        // 4 square corners: (0,0), (0,1), (1,1), (1,0)
        roa.addPoint("A", 0, 0);
        roa.addPoint("B", 0, 1);
        roa.addPoint("C", 1, 1);
        roa.addPoint("D", 1, 0);

        const result = roa.search(120, 20);
        assert.equal(result.found, true);
        assert.equal(result.tour.length, 5);
        assert.equal(result.tour[0], result.tour[result.tour.length - 1]);

        // Optimal perimeter of unit square is 4.0
        assert.equal(Math.abs(result.bestCost - 4.0) < 1e-6, true);
        assert.equal(result.bestCost <= result.initialCost, true);
    });

    it("handles single and two point graphs correctly", () => {
        const single = new DistributedRemoraOptimizationAlgorithmTSPOptimizer();
        single.addPoint("P1", 5, 5);
        const resSingle = single.search();
        assert.equal(resSingle.found, true);
        assert.equal(resSingle.bestCost, 0);
        assert.equal(resSingle.tour.length, 2);

        const pair = new DistributedRemoraOptimizationAlgorithmTSPOptimizer();
        pair.addPoint("P1", 0, 0);
        pair.addPoint("P2", 3, 4);
        const resPair = pair.search();
        assert.equal(resPair.found, true);
        assert.equal(resPair.bestCost, 10);
        assert.equal(resPair.tour.length, 3);
    });

    it("defensively handles empty graph and duplicate points", () => {
        const empty = new DistributedRemoraOptimizationAlgorithmTSPOptimizer();
        assert.equal(empty.search().found, false);

        const dup = new DistributedRemoraOptimizationAlgorithmTSPOptimizer();
        dup.addPoint("X", 0, 0);
        dup.addPoint("X", 5, 5);
        assert.equal(dup.search().tour.length, 2);
    });
});
