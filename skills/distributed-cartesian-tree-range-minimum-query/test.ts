import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedCartesianTree } from "./index.js";

describe("DistributedCartesianTree Linear Construction & Range Minimum Query", () => {
    it("builds Cartesian tree in linear O(N) time with min-heap root property", () => {
        const arr = [9, 3, 7, 1, 8, 12, 10, 20, 15, 18, 5];
        const tree = new DistributedCartesianTree(arr);

        assert.equal(tree.size, arr.length);

        // Global minimum query [0, arr.length - 1] -> Index 3 (value 1)
        const globalMin = tree.rangeMinimumQuery(0, arr.length - 1);
        assert.equal(globalMin?.minIndex, 3);
        assert.equal(globalMin?.minValue, 1);
    });

    it("queries sub-ranges correctly via Lowest Common Ancestor", () => {
        const arr = [40, 10, 20, 5, 30, 50, 15];
        const tree = new DistributedCartesianTree(arr);

        // Range [0, 2] -> values [40, 10, 20] -> Min 10 (idx 1)
        const q1 = tree.rangeMinimumQuery(0, 2);
        assert.equal(q1?.minIndex, 1);
        assert.equal(q1?.minValue, 10);

        // Range [4, 6] -> values [30, 50, 15] -> Min 15 (idx 6)
        const q2 = tree.rangeMinimumQuery(4, 6);
        assert.equal(q2?.minIndex, 6);
        assert.equal(q2?.minValue, 15);
    });

    it("defensively handles empty arrays and out-of-bound indices", () => {
        const tree = new DistributedCartesianTree();

        assert.equal(tree.size, 0);
        assert.equal(tree.rangeMinimumQuery(0, 0), null);

        tree.build([100]);
        assert.equal(tree.size, 1);
        const single = tree.rangeMinimumQuery(0, 0);
        assert.equal(single?.minValue, 100);
    });
});