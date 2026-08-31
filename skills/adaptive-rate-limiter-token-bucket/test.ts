import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { AdaptiveRateLimiter } from "./index.js";

describe("AdaptiveRateLimiter Token Bucket & Tiered Penalties", () => {
    it("permits initial burst capacity up to the configured limit", () => {
        let fakeNow = 100000;
        const limiter = new AdaptiveRateLimiter({
            capacity: 5,
            refillTokensPerSecond: 1,
            now: () => fakeNow,
        });

        // 5 requests allowed in burst
        for (let i = 0; i < 5; i++) {
            const res = limiter.consume("client_1", 1);
            assert.equal(res.allowed, true);
        }

        // 6th request rejected
        const blocked = limiter.consume("client_1", 1);
        assert.equal(blocked.allowed, false);
        assert.equal(blocked.remainingTokens, 0);
        assert.ok(blocked.retryAfterMs > 0);
    });

    it("refills tokens over time continuously", () => {
        let fakeNow = 100000;
        const limiter = new AdaptiveRateLimiter({
            capacity: 5,
            refillTokensPerSecond: 2, // 2 tokens / sec
            now: () => fakeNow,
        });

        // Drain 5 tokens
        for (let i = 0; i < 5; i++) limiter.consume("client_1", 1);
        assert.equal(limiter.consume("client_1", 1).allowed, false);

        // Advance 2.5 seconds -> refills 5 tokens
        fakeNow += 2500;
        const res = limiter.consume("client_1", 3);
        assert.equal(res.allowed, true);
        assert.equal(res.remainingTokens, 2);
    });

    it("escalates penalty tier to THROTTLED and BANNED on repeated violations", () => {
        let fakeNow = 100000;
        const limiter = new AdaptiveRateLimiter({
            capacity: 2,
            refillTokensPerSecond: 1,
            throttleThresholdViolations: 3,
            banThresholdViolations: 5,
            banDurationMs: 60000,
            now: () => fakeNow,
        });

        // Drain tokens
        limiter.consume("bad_actor", 2);

        // 1st & 2nd violation (NORMAL)
        assert.equal(limiter.consume("bad_actor", 1).tier, "NORMAL");
        assert.equal(limiter.consume("bad_actor", 1).tier, "NORMAL");

        // 3rd violation -> Escalates to THROTTLED
        const throttledRes = limiter.consume("bad_actor", 1);
        assert.equal(throttledRes.tier, "THROTTLED");

        // 4th violation
        limiter.consume("bad_actor", 1);

        // 5th violation -> Escalates to BANNED
        const bannedRes = limiter.consume("bad_actor", 1);
        assert.equal(bannedRes.tier, "BANNED");
        assert.equal(bannedRes.allowed, false);
        assert.equal(bannedRes.retryAfterMs, 60000);
    });

    it("purges stale client buckets to maintain constant memory footprint", () => {
        let fakeNow = 100000;
        const limiter = new AdaptiveRateLimiter({
            capacity: 5,
            refillTokensPerSecond: 1,
            now: () => fakeNow,
        });

        limiter.consume("ephemeral_client", 1);
        fakeNow += 700000; // Idle for 700s > 600s maxIdle

        const purged = limiter.purgeStale(600000);
        assert.equal(purged, 1);
    });
});