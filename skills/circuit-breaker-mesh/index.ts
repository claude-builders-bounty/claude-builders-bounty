/**
 * Resilient Distributed Circuit Breaker Pattern Engine for Microservices and AI Agents.
 * Implements sliding-window failure metrics, automated state transitions (CLOSED, OPEN, HALF_OPEN),
 * canary probe execution, and fallback strategies.
 */

export type CircuitBreakerState = "CLOSED" | "OPEN" | "HALF_OPEN";

export interface CircuitBreakerOptions {
    failureThresholdPercent?: number; // e.g. 50 = 50% failures trigger trip
    minimumRequests?: number;          // Min requests in window before evaluating threshold
    cooldownMs?: number;               // Time to stay OPEN before attempting HALF_OPEN probe
    halfOpenSuccessThreshold?: number; // Number of consecutive canary successes to close
    windowDurationMs?: number;         // Sliding window duration
    now?: () => number;                // Optional injected clock
}

export interface CircuitBreakerMetrics {
    state: CircuitBreakerState;
    totalRequests: number;
    successfulRequests: number;
    failedRequests: number;
    rejectedRequests: number;
    consecutiveHalfOpenSuccesses: number;
    lastStateChangeEpochMs: number;
}

export class CircuitBreakerMesh {
    private state: CircuitBreakerState = "CLOSED";
    private readonly failureThresholdPercent: number;
    private readonly minimumRequests: number;
    private readonly cooldownMs: number;
    private readonly halfOpenSuccessThreshold: number;
    private readonly windowDurationMs: number;
    private readonly now: () => number;

    private requestTimestamps: Array<{ success: boolean; epochMs: number }> = [];
    private rejectedCount = 0;
    private halfOpenSuccessCount = 0;
    private lastStateChangeMs: number;

    constructor(options: CircuitBreakerOptions = {}) {
        this.failureThresholdPercent = options.failureThresholdPercent ?? 50;
        this.minimumRequests = options.minimumRequests ?? 5;
        this.cooldownMs = options.cooldownMs ?? 10000;
        this.halfOpenSuccessThreshold = options.halfOpenSuccessThreshold ?? 3;
        this.windowDurationMs = options.windowDurationMs ?? 30000;
        this.now = options.now ?? Date.now;
        this.lastStateChangeMs = this.now();
    }

    private pruneOldRequests(now: number): void {
        const cutoff = now - this.windowDurationMs;
        this.requestTimestamps = this.requestTimestamps.filter(r => r.epochMs >= cutoff);
    }

    public getState(now: number = this.now()): CircuitBreakerState {
        if (this.state === "OPEN") {
            if (now - this.lastStateChangeMs >= this.cooldownMs) {
                this.state = "HALF_OPEN";
                this.halfOpenSuccessCount = 0;
                this.lastStateChangeMs = now;
            }
        }
        return this.state;
    }

    public async execute<T>(
        action: () => Promise<T>,
        fallback?: (error?: Error) => T | Promise<T>
    ): Promise<T> {
        const now = this.now();
        const currentState = this.getState(now);

        if (currentState === "OPEN") {
            this.rejectedCount++;
            if (fallback) {
                return fallback(new Error("CircuitBreaker is OPEN"));
            }
            throw new Error("CircuitBreaker is OPEN (Fast-Fail)");
        }

        try {
            const result = await action();
            this.recordSuccess(now);
            return result;
        } catch (err: any) {
            this.recordFailure(now);
            if (fallback) {
                return fallback(err);
            }
            throw err;
        }
    }

    private recordSuccess(now: number): void {
        this.pruneOldRequests(now);
        this.requestTimestamps.push({ success: true, epochMs: now });

        if (this.state === "HALF_OPEN") {
            this.halfOpenSuccessCount++;
            if (this.halfOpenSuccessCount >= this.halfOpenSuccessThreshold) {
                this.state = "CLOSED";
                this.lastStateChangeMs = now;
                this.requestTimestamps = []; // Reset window on recovery
            }
        }
    }

    private recordFailure(now: number): void {
        this.pruneOldRequests(now);
        this.requestTimestamps.push({ success: false, epochMs: now });

        if (this.state === "HALF_OPEN") {
            // Any failure in HALF_OPEN trips immediately back to OPEN
            this.state = "OPEN";
            this.lastStateChangeMs = now;
            this.halfOpenSuccessCount = 0;
            return;
        }

        if (this.state === "CLOSED") {
            if (this.requestTimestamps.length >= this.minimumRequests) {
                const failures = this.requestTimestamps.filter(r => !r.success).length;
                const failureRate = (failures / this.requestTimestamps.length) * 100;

                if (failureRate >= this.failureThresholdPercent) {
                    this.state = "OPEN";
                    this.lastStateChangeMs = now;
                }
            }
        }
    }

    public getMetrics(now: number = this.now()): CircuitBreakerMetrics {
        this.pruneOldRequests(now);
        const successes = this.requestTimestamps.filter(r => r.success).length;
        const failures = this.requestTimestamps.filter(r => !r.success).length;

        return {
            state: this.getState(now),
            totalRequests: this.requestTimestamps.length,
            successfulRequests: successes,
            failedRequests: failures,
            rejectedRequests: this.rejectedCount,
            consecutiveHalfOpenSuccesses: this.halfOpenSuccessCount,
            lastStateChangeEpochMs: this.lastStateChangeMs,
        };
    }
}