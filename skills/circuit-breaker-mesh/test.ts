import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { CircuitBreakerMesh } from "./index.js";

describe("CircuitBreakerMesh Distributed Resiliency", () => {
    it("executes successful actions normally in CLOSED state", async () => {
        const cb = new CircuitBreakerMesh({ minimumRequests: 3 });
        const result = await cb.execute(async () => "ok");
        assert.equal(result, "ok");
        assert.equal(cb.getState(), "CLOSED");
    });

    it("trips to OPEN when failure threshold is exceeded", async () => {
        const cb = new CircuitBreakerMesh({
            minimumRequests: 4,
            failureThresholdPercent: 50,
            cooldownMs: 5000,
        });

        // 2 successes, 2 failures => 50% failure rate
        await cb.execute(async () => "ok1");
        await cb.execute(async () => "ok2");
        await cb.execute(async () => { throw new Error("err1"); }, () => "fallback");
        await cb.execute(async () => { throw new Error("err2"); }, () => "fallback");

        assert.equal(cb.getState(), "OPEN");

        // Subsequent call fails fast or uses fallback
        const fallbackRes = await cb.execute(async () => "won't run", () => "fallback_active");
        assert.equal(fallbackRes, "fallback_active");
    });

    it("recovers through HALF_OPEN canary verification", async () => {
        let fakeTime = 100000;
        const cb = new CircuitBreakerMesh({
            minimumRequests: 2,
            failureThresholdPercent: 50,
            cooldownMs: 1000,
            halfOpenSuccessThreshold: 2,
            now: () => fakeTime,
        });

        // Trip breaker
        await cb.execute(async () => { throw new Error("fail1"); }, () => "f");
        await cb.execute(async () => { throw new Error("fail2"); }, () => "f");
        assert.equal(cb.getState(), "OPEN");

        // Advance past cooldown
        fakeTime += 1500;
        assert.equal(cb.getState(), "HALF_OPEN");

        // 1st canary success
        await cb.execute(async () => "canary1");
        // 2nd canary success -> should close
        await cb.execute(async () => "canary2");

        assert.equal(cb.getState(), "CLOSED");
    });
});