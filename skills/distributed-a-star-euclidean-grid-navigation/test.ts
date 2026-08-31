import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedAStarGrid } from "./index.js";

describe("DistributedAStarGrid Optimal Pathfinding", () => {
    it("finds optimal Euclidean obstacle-avoiding path on 2D grid", () => {
        const grid = new DistributedAStarGrid(10, 10, true);

        // Place wall obstacle at x = 3, y = 0 to 7
        for (let y = 0; y <= 7; y++) {
            grid.setObstacle(3, y, true);
        }

        const start = { x: 0, y: 0 };
        const goal = { x: 5, y: 0 };

        const result = grid.findPath(start, goal, "EUCLIDEAN");
        assert.equal(result.found, true);
        assert.equal(result.path[0].x, 0);
        assert.equal(result.path[0].y, 0);
        assert.equal(result.path[result.path.length - 1].x, 5);
        assert.equal(result.path[result.path.length - 1].y, 0);
        assert.equal(result.totalCost > 5, true); // Must circumnavigate wall
    });

    it("returns found: false when goal is completely enclosed by obstacles", () => {
        const grid = new DistributedAStarGrid(5, 5, false);

        grid.setObstacle(3, 4, true);
        grid.setObstacle(4, 3, true);

        const result = grid.findPath({ x: 0, y: 0 }, { x: 4, y: 4 }, "MANHATTAN");
        assert.equal(result.found, false);
        assert.deepEqual(result.path, []);
    });

    it("defensively handles out-of-bounds start/goal coordinates and start on obstacle", () => {
        const grid = new DistributedAStarGrid(5, 5);

        grid.setObstacle(1, 1, true);

        assert.equal(grid.findPath({ x: 1, y: 1 }, { x: 4, y: 4 }).found, false);
        assert.equal(grid.findPath({ x: -1, y: 0 }, { x: 4, y: 4 }).found, false);
        assert.equal(grid.findPath({ x: 0, y: 0 }, { x: 10, y: 10 }).found, false);
    });
});