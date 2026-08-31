import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedScatterSearchTSP } from "./index.js";

describe("DistributedScatterSearchTSP Optimization", () => {
    it("combines reference set solutions with path relinking and converges to optimal square perimeter", () => {
        const ss = new DistributedScatterSearchTSP();

        // 4 square corners in crossed order: (0,0), (1,1), (0,1), (1,0)
        ss.addPoint("A", 0, 0);
        ss.addPoint("B", 1, 1);
        ss.addPoint("C", 0, 1);
        ss.addPoint("D", 1, 0);

        const result = ss.search(20, 6);
        assert.equal(result.found, true);
        assert.equal(result.tour.length, 5);
        assert.equal(result.tour[0], result.tour[result.tour.length - 1]);

        // Optimal perimeter of square is 4.0
        assert.equal(Math.abs(result.bestCost - 4.0) < 1e-6, true);
        assert.equal(result.bestCost <= result.initialCost, true);
    });

    it("handles single and two point graphs correctly", () => {
        const single = new DistributedScatterSearchTSP();
        single.addPoint("P1", 5, 5);
        const resSingle = single.search();
        assert.equal(resSingle.found, true);
        assert.equal(resSingle.bestCost, 0);

        const pair = new DistributedScatterSearchTSP();
        pair.addPoint("P1", 0, 0);
        pair.addPoint("P2", 3, 4);
        const resPair = pair.search();
        assert.equal(resPair.found, true);
        assert.equal(resPair.bestCost, 10);
    });

    it("defensively handles empty graph and duplicate points", () => {
        const empty = new DistributedScatterSearchTSP();
        assert.equal(empty.search().found, false);

        const dup = new DistributedScatterSearchTSP();
        dup.addPoint("X", 0, 0);
        dup.addPoint("X", 5, 5);
        assert.equal(dup.search().tour.length, 2);
    });
});