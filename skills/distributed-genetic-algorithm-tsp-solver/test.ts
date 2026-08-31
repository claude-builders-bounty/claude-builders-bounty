import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedGeneticTSP } from "./index.js";

describe("DistributedGeneticTSP Evolutionary Optimization", () => {
    it("evolves population and converges to optimal perimeter cost on unit square", () => {
        const ga = new DistributedGeneticTSP();

        // 4 square corners
        ga.addPoint("A", 0, 0);
        ga.addPoint("B", 0, 1);
        ga.addPoint("C", 1, 1);
        ga.addPoint("D", 1, 0);

        const result = ga.evolve(30, 50, 0.2);
        assert.equal(result.found, true);
        assert.equal(result.tour.length, 5);
        assert.equal(result.tour[0], result.tour[result.tour.length - 1]);

        // Optimal perimeter of square is 4.0
        assert.equal(Math.abs(result.bestCost - 4.0) < 1e-6, true);
        assert.equal(result.bestCost <= result.initialBestCost, true);
    });

    it("handles single and two point graphs correctly", () => {
        const single = new DistributedGeneticTSP();
        single.addPoint("P1", 5, 5);
        const resSingle = single.evolve();
        assert.equal(resSingle.found, true);
        assert.equal(resSingle.bestCost, 0);

        const pair = new DistributedGeneticTSP();
        pair.addPoint("P1", 0, 0);
        pair.addPoint("P2", 3, 4);
        const resPair = pair.evolve();
        assert.equal(resPair.found, true);
        assert.equal(resPair.bestCost, 10);
    });

    it("defensively handles empty graph and duplicate points", () => {
        const empty = new DistributedGeneticTSP();
        assert.equal(empty.evolve().found, false);

        const dup = new DistributedGeneticTSP();
        dup.addPoint("X", 0, 0);
        dup.addPoint("X", 5, 5);
        assert.equal(dup.evolve().tour.length, 2);
    });
});