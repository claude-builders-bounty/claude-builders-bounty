import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedHyperLogLog } from "./index.js";

describe("DistributedHyperLogLog Cardinality Estimation & Distributed Merge", () => {
    it("accurately estimates unique cardinality within reasonable error bounds", () => {
        const hll = new DistributedHyperLogLog(8); // 256 registers

        for (let i = 0; i < 500; i++) {
            hll.add(`user_session_${i}`);
        }

        const est = hll.count();
        // 500 unique elements should estimate within +/- 15%
        assert.ok(est >= 400 && est <= 600, `Estimated count ${est} outside expected range`);
    });

    it("merges two independent HLL states accurately", () => {
        const hllA = new DistributedHyperLogLog(8);
        const hllB = new DistributedHyperLogLog(8);

        for (let i = 0; i < 200; i++) {
            hllA.add(`element_${i}`);
        }
        for (let i = 200; i < 400; i++) {
            hllB.add(`element_${i}`);
        }

        hllA.merge(hllB);
        const totalEst = hllA.count();

        // 400 distinct items total
        assert.ok(totalEst >= 320 && totalEst <= 480, `Merged estimate ${totalEst} outside expected range`);
    });
});