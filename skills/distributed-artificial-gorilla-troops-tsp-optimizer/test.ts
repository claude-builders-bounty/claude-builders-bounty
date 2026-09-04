import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedArtificialGorillaTroopsTSPOptimizer } from "./index.js";

describe("DistributedArtificialGorillaTroopsTSPOptimizer Troop & Silverback Metaheuristic", () => {
    it("simulates gorilla troop migration & silverback leadership, optimizing unit square perimeter", () => {
        const gto = new DistributedArtificialGorillaTroopsTSPOptimizer();

        // 4 square corners: (0,0), (0,1), (1,1), (1,0)
        gto.addPoint("A", 0, 0);
        gto.addPoint("B", 0, 1);
        gto.addPoint("C", 1, 1);
        gto.addPoint("D", 1, 0);

        const result = gto.search(120, 20);
        assert.equal(result.found, true);
        assert.equal(result.tour.length, 5);
        assert.equal(result.tour[0], result.tour[result.tour.length - 1]);

        // Optimal perimeter of square is 4.0
        assert.equal(Math.abs(result.bestCost - 4.0) < 1e-6, true);
        assert.equal(result.bestCost <= result.initialCost, true);
    });

    it("handles single and two point graphs correctly", () => {
        const single = new DistributedArtificialGorillaTroopsTSPOptimizer();
        single.addPoint("P1", 5, 5);
        const resSingle = single.search();
        assert.equal(resSingle.found, true);
        assert.equal(resSingle.bestCost, 0);
        assert.equal(resSingle.tour.length, 2);

        const pair = new DistributedArtificialGorillaTroopsTSPOptimizer();
        pair.addPoint("P1", 0, 0);
        pair.addPoint("P2", 3, 4);
        const resPair = pair.search();
        assert.equal(resPair.found, true);
        assert.equal(resPair.bestCost, 10);
        assert.equal(resPair.tour.length, 3);
    });

    it("defensively handles empty graph and duplicate points", () => {
        const empty = new DistributedArtificialGorillaTroopsTSPOptimizer();
        assert.equal(empty.search().found, false);

        const dup = new DistributedArtificialGorillaTroopsTSPOptimizer();
        dup.addPoint("X", 0, 0);
        dup.addPoint("X", 5, 5);
        assert.equal(dup.search().tour.length, 2);
    });
});