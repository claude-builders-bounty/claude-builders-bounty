import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedFenwickTree, DistributedFenwickTree2D } from "./index.js";

describe("DistributedFenwickTree 1D & 2D Cumulative Frequency Operations", () => {
    it("updates point values and computes accurate 1D range sums in O(log N)", () => {
        const bit = new DistributedFenwickTree(10);

        // Array: [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for (let i = 1; i <= 10; i++) {
            bit.add(i, i * 10);
        }

        assert.equal(bit.query(3), 60); // 10 + 20 + 30
        assert.equal(bit.queryRange(2, 4), 90); // 20 + 30 + 40
        assert.equal(bit.queryRange(1, 10), 550);

        // Update point 3 with +5
        bit.add(3, 5);
        assert.equal(bit.query(3), 65);
        assert.equal(bit.queryRange(2, 4), 95);
    });

    it("performs 2D sub-grid rectangle prefix updates and range queries", () => {
        const bit2d = new DistributedFenwickTree2D(5, 5);

        bit2d.add(2, 2, 10);
        bit2d.add(3, 3, 20);

        assert.equal(bit2d.query(2, 2), 10);
        assert.equal(bit2d.query(3, 3), 30);
        assert.equal(bit2d.queryRectangle(2, 2, 3, 3), 30);
        assert.equal(bit2d.queryRectangle(3, 3, 3, 3), 20);
    });

    it("defensively handles out-of-bounds indices and non-finite values", () => {
        const bit = new DistributedFenwickTree(5);

        bit.add(0, 10); // 0 is invalid 1-based index
        bit.add(99, 10);
        bit.add(1, NaN);

        assert.equal(bit.query(0), 0);
        assert.equal(bit.query(null as any), 0);
        assert.equal(bit.queryRange(5, 2), 0);
    });
});