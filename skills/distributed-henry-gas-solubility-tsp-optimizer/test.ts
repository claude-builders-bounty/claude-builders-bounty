import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedHenryGasSolubilityTSPOptimizer } from "./index.js";

describe("DistributedHenryGasSolubilityTSPOptimizer Swarm Metaheuristic", () => {
    it("simulates gas cluster solubility and Henry laws, optimizing unit square perimeter", () => {
        const hgso = new DistributedHenryGasSolubilityTSPOptimizer();

        // 4 square corners: (0,0), (0,1), (1,1), (1,0)
        hgso.addPoint("A", 0, 0);
        hgso.addPoint("B", 0, 1);
        hgso.addPoint("C", 1, 1);
        hgso.addPoint("D", 1, 0);

        const result = hgso.search(120, 16, 4);
        assert.equal(result.found, true);
        assert.equal(result.tour.length, 5);
        assert.equal(result.tour[0], result.tour[result.tour.length - 1]);

        // Optimal perimeter of square is 4.0
        assert.equal(Math.abs(result.bestCost - 4.0) < 1e-6, true);
        assert.equal(result.bestCost <= result.initialCost, true);
    });

    it("handles single and two point graphs correctly", () => {
        const single = new DistributedHenryGasSolubilityTSPOptimizer();
        single.addPoint("P1", 5, 5);
        const resSingle = single.search();
        assert.equal(resSingle.found, true);
        assert.equal(resSingle.bestCost, 0);

        const pair = new DistributedHenryGasSolubilityTSPOptimizer();
        pair.addPoint("P1", 0, 0);
        pair.addPoint("P2", 3, 4);
        const resPair = pair.search();
        assert.equal(resPair.found, true);
        assert.equal(resPair.bestCost, 10);
    });

    it("defensively handles empty graph and duplicate points", () => {
        const empty = new DistributedHenryGasSolubilityTSPOptimizer();
        assert.equal(empty.search().found, false);

        const dup = new DistributedHenryGasSolubilityTSPOptimizer();
        dup.addPoint("X", 0, 0);
        dup.addPoint("X", 5, 5);
        assert.equal(dup.search().tour.length, 2);
    });
});