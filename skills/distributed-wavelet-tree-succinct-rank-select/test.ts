import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedWaveletTree } from "./index.js";

describe("DistributedWaveletTree Succinct Rank & Range Quantile Operations", () => {
    it("computes exact range quantiles (k-th smallest element) in O(log Sigma)", () => {
        // 1-based data: [1, 5, 2, 4, 3, 6, 8, 7, 2, 1]
        const data = [1, 5, 2, 4, 3, 6, 8, 7, 2, 1];
        const wt = new DistributedWaveletTree(data);

        assert.equal(wt.size, 10);

        // Subarray [2, 6] -> [5, 2, 4, 3, 6] -> Sorted: [2, 3, 4, 5, 6]
        // 1st smallest = 2
        assert.equal(wt.quantile(2, 6, 1), 2);
        // 3rd smallest = 4
        assert.equal(wt.quantile(2, 6, 3), 4);
        // 5th smallest = 6
        assert.equal(wt.quantile(2, 6, 5), 6);
    });

    it("evaluates symbol prefix rank accurately", () => {
        const data = [10, 20, 10, 30, 20, 10, 40];
        const wt = new DistributedWaveletTree(data);

        // Rank of symbol 10 up to index 3 -> 2 occurrences
        assert.equal(wt.rank(10, 3), 2);
        // Rank of symbol 10 up to index 6 -> 3 occurrences
        assert.equal(wt.rank(10, 6), 3);
        // Rank of symbol 20 up to index 5 -> 2 occurrences
        assert.equal(wt.rank(20, 5), 2);
        // Out of bound symbol rank -> 0
        assert.equal(wt.rank(999, 5), 0);
    });

    it("defensively handles empty structures and out-of-range queries", () => {
        const emptyWt = new DistributedWaveletTree([]);
        assert.equal(emptyWt.size, 0);
        assert.equal(emptyWt.quantile(1, 5, 1), null);
        assert.equal(emptyWt.rank(10, 5), 0);
    });
});