import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedTwoOptTSP } from "./index.js";

describe("DistributedTwoOptTSP 2-Opt Local Search", () => {
    it("untangles crossed tour on square corners and achieves optimal perimeter cost", () => {
        const tsp = new DistributedTwoOptTSP();

        // Points in crossed order: (0,0), (1,1), (0,1), (1,0) -> Hourglass shape
        tsp.addPoint("A", 0, 0);
        tsp.addPoint("B", 1, 1);
        tsp.addPoint("C", 0, 1);
        tsp.addPoint("D", 1, 0);

        const result = tsp.optimize();
        assert.equal(result.found, true);
        assert.equal(result.tour.length, 5); // 4 points + return to start
        assert.equal(result.tour[0], result.tour[result.tour.length - 1]);

        // Optimal uncrossed square perimeter is 4.0
        assert.equal(Math.abs(result.optimizedCost - 4.0) < 1e-6, true);
        assert.equal(result.optimizedCost < result.initialCost, true);
        assert.equal(result.improvementsCount >= 1, true);
    });

    it("handles single and two point graphs correctly", () => {
        const single = new DistributedTwoOptTSP();
        single.addPoint("P1", 5, 5);
        const resSingle = single.optimize();
        assert.equal(resSingle.found, true);
        assert.equal(resSingle.optimizedCost, 0);

        const pair = new DistributedTwoOptTSP();
        pair.addPoint("P1", 0, 0);
        pair.addPoint("P2", 3, 4);
        const resPair = pair.optimize();
        assert.equal(resPair.found, true);
        assert.equal(resPair.optimizedCost, 10);
    });

    it("defensively handles empty graph and duplicate points", () => {
        const empty = new DistributedTwoOptTSP();
        assert.equal(empty.optimize().found, false);

        const dup = new DistributedTwoOptTSP();
        dup.addPoint("X", 0, 0);
        dup.addPoint("X", 5, 5); // Duplicate ID ignored
        assert.equal(dup.optimize().tour.length, 2);
    });
});