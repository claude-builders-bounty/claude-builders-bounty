import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedSlidingWindowCounter } from "./index.js";

describe("DistributedSlidingWindowCounter Granular Slicing", () => {
    it("permits requests up to quota within sliding window", () => {
        let fakeNow = 100000;
        const limiter = new DistributedSlidingWindowCounter({
            windowSizeMs: 10000,
            sliceCount: 10,
            maxRequestsPerWindow: 5,
            now: () => fakeNow,
        });

        for (let i = 0; i < 5; i++) {
            const dec = limiter.record("user_1", 1);
            assert.equal(dec.allowed, true);
        }

        const blocked = limiter.record("user_1", 1);
        assert.equal(blocked.allowed, false);
        assert.equal(blocked.remainingQuota, 0);
    });

    it("slides window forward and reclaims quota as time slices expire", () => {
        let fakeNow = 100000;
        const limiter = new DistributedSlidingWindowCounter({
            windowSizeMs: 10000,
            sliceCount: 10,
            maxRequestsPerWindow: 4,
            now: () => fakeNow,
        });

        limiter.record("user_2", 4); // Exhaust quota
        assert.equal(limiter.record("user_2", 1).allowed, false);

        // Advance past window duration
        fakeNow += 11000;

        const recovered = limiter.record("user_2", 2);
        assert.equal(recovered.allowed, true);
        assert.equal(recovered.remainingQuota, 2);
    });
});