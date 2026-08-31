import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedChristofidesTSP } from "./index.js";

describe("DistributedChristofidesTSP 1.5-Approximation", () => {
    it("computes metric TSP tour for 4 square vertices with exact optimal perimeter cost", () => {
        const tsp = new DistributedChristofidesTSP();

        // 4 corners of unit square: (0,0), (0,1), (1,1), (1,0)
        tsp.addPoint("A", 0, 0);
        tsp.addPoint("B", 0, 1);
        tsp.addPoint("C", 1, 1);
        tsp.addPoint("D", 1, 0);

        const result = tsp.computeTour();
        assert.equal(result.found, true);
        assert.equal(result.pointsCount, 4);
        assert.equal(result.tour.length, 5); // 4 points + return to start
        assert.equal(result.tour[0], result.tour[result.tour.length - 1]);

        // Optimal perimeter of square is 4.0
        assert.equal(Math.abs(result.tourCost - 4.0) < 1e-6, true);
    });

    it("handles single and two point graphs correctly", () => {
        const single = new DistributedChristofidesTSP();
        single.addPoint("P1", 5, 5);
        const resSingle = single.computeTour();
        assert.equal(resSingle.found, true);
        assert.equal(resSingle.tourCost, 0);

        const pair = new DistributedChristofidesTSP();
        pair.addPoint("P1", 0, 0);
        pair.addPoint("P2", 3, 4); // Distance 5
        const resPair = pair.computeTour();
        assert.equal(resPair.found, true);
        assert.equal(resPair.tourCost, 10);
    });

    it("defensively handles empty graph and duplicate points", () => {
        const empty = new DistributedChristofidesTSP();
        assert.equal(empty.computeTour().found, false);

        const dup = new DistributedChristofidesTSP();
        dup.addPoint("X", 0, 0);
        dup.addPoint("X", 5, 5); // Duplicate ID ignored
        assert.equal(dup.computeTour().pointsCount, 1);
    });
});