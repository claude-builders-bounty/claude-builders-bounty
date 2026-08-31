import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedGraspTSP } from "./index.js";

describe("DistributedGraspTSP Metaheuristic", () => {
    it("constructs and optimizes unit square vertices converging to optimal perimeter", () => {
        const grasp = new DistributedGraspTSP();

        // 4 square corners: (0,0), (0,1), (1,1), (1,0)
        grasp.addPoint("A", 0, 0);
        grasp.addPoint("B", 0, 1);
        grasp.addPoint("C", 1, 1);
        grasp.addPoint("D", 1, 0);

        const result = grasp.optimize(20, 0.3);
        assert.equal(result.found, true);
        assert.equal(result.tour.length, 5);
        assert.equal(result.tour[0], result.tour[result.tour.length - 1]);

        // Optimal perimeter of square is 4.0
        assert.equal(Math.abs(result.bestCost - 4.0) < 1e-6, true);
    });

    it("handles single and two point graphs correctly", () => {
        const single = new DistributedGraspTSP();
        single.addPoint("P1", 5, 5);
        const resSingle = single.optimize();
        assert.equal(resSingle.found, true);
        assert.equal(resSingle.bestCost, 0);

        const pair = new DistributedGraspTSP();
        pair.addPoint("P1", 0, 0);
        pair.addPoint("P2", 3, 4);
        const resPair = pair.optimize();
        assert.equal(resPair.found, true);
        assert.equal(resPair.bestCost, 10);
    });

    it("defensively handles empty graph and duplicate points", () => {
        const empty = new DistributedGraspTSP();
        assert.equal(empty.optimize().found, false);

        const dup = new DistributedGraspTSP();
        dup.addPoint("X", 0, 0);
        dup.addPoint("X", 5, 5);
        assert.equal(dup.optimize().tour.length, 2);
    });
});