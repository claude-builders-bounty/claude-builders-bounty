import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedSimulatedAnnealingTSP } from "./index.js";

describe("DistributedSimulatedAnnealingTSP Thermodynamic Optimization", () => {
    it("untangles crossed tour on square corners and converges to perimeter cost", () => {
        const sa = new DistributedSimulatedAnnealingTSP();

        // Points in crossed order: (0,0), (1,1), (0,1), (1,0) -> Hourglass shape (cost ~5.65)
        sa.addPoint("A", 0, 0);
        sa.addPoint("B", 1, 1);
        sa.addPoint("C", 0, 1);
        sa.addPoint("D", 1, 0);

        const result = sa.anneal(500, 0.99, 1e-4, 5000);
        assert.equal(result.found, true);
        assert.equal(result.tour.length, 5); // 4 points + return to start
        assert.equal(result.tour[0], result.tour[result.tour.length - 1]);

        // Optimal perimeter of uncrossed square is 4.0
        assert.equal(Math.abs(result.bestCost - 4.0) < 1e-6, true);
        assert.equal(result.bestCost <= result.initialCost, true);
    });

    it("handles single and two point graphs correctly", () => {
        const single = new DistributedSimulatedAnnealingTSP();
        single.addPoint("P1", 5, 5);
        const resSingle = single.anneal();
        assert.equal(resSingle.found, true);
        assert.equal(resSingle.bestCost, 0);

        const pair = new DistributedSimulatedAnnealingTSP();
        pair.addPoint("P1", 0, 0);
        pair.addPoint("P2", 3, 4);
        const resPair = pair.anneal();
        assert.equal(resPair.found, true);
        assert.equal(resPair.bestCost, 10);
    });

    it("defensively handles empty graph and duplicate points", () => {
        const empty = new DistributedSimulatedAnnealingTSP();
        assert.equal(empty.anneal().found, false);

        const dup = new DistributedSimulatedAnnealingTSP();
        dup.addPoint("X", 0, 0);
        dup.addPoint("X", 5, 5); // Duplicate ID ignored
        assert.equal(dup.anneal().tour.length, 2);
    });
});