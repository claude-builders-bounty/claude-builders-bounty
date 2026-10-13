import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { DistributedPelicanOptimizationAlgorithmTSPOptimizer } from "./index.ts";

describe("DistributedPelicanOptimizationAlgorithmTSPOptimizer Metaheuristic", () => {
    it("simulates aerial soaring, plunge diving, and gular scoop optimizing unit square perimeter", () => {
        const optimizer = new DistributedPelicanOptimizationAlgorithmTSPOptimizer();
        // 4 corners of a unit square: perimeter is 4.0
        optimizer.addPoint("A", 0, 0);
        optimizer.addPoint("B", 1, 0);
        optimizer.addPoint("C", 1, 1);
        optimizer.addPoint("D", 0, 1);

        const result = optimizer.search(40, 15);

        assert.equal(result.found, true);
        assert.equal(result.iterationsCompleted, 40);
        assert.equal(result.tour.length, 5); // 4 points + return to start
        assert.equal(result.tour[0], result.tour[result.tour.length - 1]);

        // Optimum perimeter for unit square is 4.0
        assert.ok(Math.abs(result.bestCost - 4.0) < 1e-5, `Expected 4.0, got ${result.bestCost}`);
        assert.ok(result.bestCost <= result.initialCost);
    });

    it("handles single and two point graphs correctly", () => {
        const single = new DistributedPelicanOptimizationAlgorithmTSPOptimizer();
        single.addPoint("P1", 10, 20);
        const singleRes = single.search(10, 5);
        assert.equal(singleRes.found, true);
        assert.equal(singleRes.bestCost, 0);
        assert.deepEqual(singleRes.tour, ["P1", "P1"]);

        const pair = new DistributedPelicanOptimizationAlgorithmTSPOptimizer();
        pair.addPoint("P1", 0, 0);
        pair.addPoint("P2", 3, 4);
        const pairRes = pair.search(10, 5);
        assert.equal(pairRes.found, true);
        assert.equal(pairRes.bestCost, 10); // 5 + 5
        assert.deepEqual(pairRes.tour, ["P1", "P2", "P1"]);
    });

    it("defensively handles empty graph and duplicate points", () => {
        const empty = new DistributedPelicanOptimizationAlgorithmTSPOptimizer();
        const emptyRes = empty.search(10, 5);
        assert.equal(emptyRes.found, false);
        assert.equal(emptyRes.tour.length, 0);

        const dup = new DistributedPelicanOptimizationAlgorithmTSPOptimizer();
        dup.addPoint("A", 0, 0);
        dup.addPoint("A", 5, 5); // Duplicate ID ignored
        dup.addPoint("", 1, 1); // Invalid ID ignored
        dup.addPoint("B", NaN, 2); // Invalid coordinate ignored
        dup.addPoint("C", 0, 1);

        const dupRes = dup.search(10, 5);
        assert.equal(dupRes.found, true);
        assert.equal(dupRes.tour.length, 3); // 2 points (A, C) -> tour A, C, A
    });
});
