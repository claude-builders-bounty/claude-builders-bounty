import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedSineCosineTSPOptimizer } from "./index.js";

describe("DistributedSineCosineTSPOptimizer Trigonometric Metaheuristic", () => {
    it("oscillates via sine and cosine transitions, converging on optimal unit square perimeter", () => {
        const sca = new DistributedSineCosineTSPOptimizer();

        // 4 square corners: (0,0), (0,1), (1,1), (1,0)
        sca.addPoint("A", 0, 0);
        sca.addPoint("B", 0, 1);
        sca.addPoint("C", 1, 1);
        sca.addPoint("D", 1, 0);

        const result = sca.search(120, 15);
        assert.equal(result.found, true);
        assert.equal(result.tour.length, 5);
        assert.equal(result.tour[0], result.tour[result.tour.length - 1]);

        // Optimal perimeter of square is 4.0
        assert.equal(Math.abs(result.bestCost - 4.0) < 1e-6, true);
        assert.equal(result.bestCost <= result.initialCost, true);
    });

    it("handles single and two point graphs correctly", () => {
        const single = new DistributedSineCosineTSPOptimizer();
        single.addPoint("P1", 5, 5);
        const resSingle = single.search();
        assert.equal(resSingle.found, true);
        assert.equal(resSingle.bestCost, 0);

        const pair = new DistributedSineCosineTSPOptimizer();
        pair.addPoint("P1", 0, 0);
        pair.addPoint("P2", 3, 4);
        const resPair = pair.search();
        assert.equal(resPair.found, true);
        assert.equal(resPair.bestCost, 10);
    });

    it("defensively handles empty graph and duplicate points", () => {
        const empty = new DistributedSineCosineTSPOptimizer();
        assert.equal(empty.search().found, false);

        const dup = new DistributedSineCosineTSPOptimizer();
        dup.addPoint("X", 0, 0);
        dup.addPoint("X", 5, 5);
        assert.equal(dup.search().tour.length, 2);
    });
});