import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedHyperLogLog } from "./index.js";

describe("DistributedHyperLogLog Distinct Element Estimation", () => {
    it("estimates distinct counts with low error on uniform inputs", () => {
        const hll = new DistributedHyperLogLog(10);

        const uniqueItems = 500;
        for (let i = 0; i < uniqueItems; i++) {
            hll.add(`user_session_${i}`);
        }

        // Add duplicates
        for (let i = 0; i < 200; i++) {
            hll.add(`user_session_${i}`);
        }

        const estimate = hll.count();
        const errorPercent = Math.abs(estimate - uniqueItems) / uniqueItems;

        assert.ok(errorPercent < 0.15, `Expected error < 15%, got ${(errorPercent * 100).toFixed(2)}%`);
    });

    it("losslessly merges registers across distributed shards", () => {
        const shard1 = new DistributedHyperLogLog(10);
        const shard2 = new DistributedHyperLogLog(10);

        for (let i = 0; i < 300; i++) {
            shard1.add(`event_${i}`);
        }
        for (let i = 250; i < 600; i++) {
            shard2.add(`event_${i}`);
        }

        shard1.merge(shard2);
        const mergedEstimate = shard1.count();

        // Total unique = 600
        const errorPercent = Math.abs(mergedEstimate - 600) / 600;
        assert.ok(errorPercent < 0.15);
    });

    it("defensively handles empty items and precision mismatch", () => {
        const hll = new DistributedHyperLogLog(10);
        const otherMismatch = new DistributedHyperLogLog(8);

        hll.add("");
        hll.add(null as any);
        assert.equal(hll.count(), 0);

        assert.throws(() => hll.merge(otherMismatch), /Cannot merge HyperLogLog/);
    });
});