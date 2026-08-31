import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedAntColonyTSP } from "./index.js";

describe("DistributedAntColonyTSP Swarm Intelligence Optimization", () => {
    it("optimizes crossed tour on square vertices and converges to perimeter cost", () => {
        const acs = new DistributedAntColonyTSP();

        // Points in crossed order: (0,0), (1,1), (0,1), (1,0)
        acs.addPoint("A", 0, 0);
        acs.addPoint("B", 1, 1);
        acs.addPoint("C", 0, 1);
        acs.addPoint("D", 1, 0);

        const result = acs.optimize(15, 30);
        assert.equal(result.found, true);
        assert.equal(result.tour.length, 5); // 4 points + return to start
        assert.equal(result.tour[0], result.tour[result.tour.length - 1]);

        // Optimal perimeter of uncrossed square is 4.0
        assert.equal(Math.abs(result.bestCost - 4.0) < 1e-6, true);
    });

    it("handles single and two point graphs correctly", () => {
        const single = new DistributedAntColonyTSP();
        single.addPoint("P1", 5, 5);
        const resSingle = single.optimize();
        assert.equal(resSingle.found, true);
        assert.equal(resSingle.bestCost, 0);

        const pair = new DistributedAntColonyTSP();
        pair.addPoint("P1", 0, 0);
        pair.addPoint("P2", 3, 4);
        const resPair = pair.optimize();
        assert.equal(resPair.found, true);
        assert.equal(resPair.bestCost, 10);
    });

    it("defensively handles empty graph and duplicate points", () => {
        const empty = new DistributedAntColonyTSP();
        assert.equal(empty.optimize().found, false);

        const dup = new DistributedAntColonyTSP();
        dup.addPoint("X", 0, 0);
        dup.addPoint("X", 5, 5); // Duplicate ID ignored
        assert.equal(dup.optimize().tour.length, 2);
    });
});