/**
 * Adaptive Token Bucket Rate Limiter with Sliding Window Penalty Escalation.
 * Enterprise-grade rate limiting featuring continuous token replenishment,
 * tiered violation penalties (NORMAL -> THROTTLED -> BANNED), automated stale
 * key eviction to prevent memory leaks, and injectable deterministic time.
 */

export type RateLimiterTier = "NORMAL" | "THROTTLED" | "BANNED";

export interface RateLimiterOptions {
    capacity: number;                  // Maximum tokens in bucket (burst limit)
    refillTokensPerSecond: number;     // Tokens replenished per second
    violationWindowMs?: number;        // Window for tracking consecutive rate limit breaches (default 60s)
    throttleThresholdViolations?: number; // Violations before entering THROTTLED (default 3)
    banThresholdViolations?: number;      // Violations before entering BANNED (default 10)
    banDurationMs?: number;            // Ban duration in milliseconds (default 5m)
    now?: () => number;                // Injectable clock (ms)
}

export interface ClientBucketState {
    tokens: number;
    lastRefillMs: number;
    violationsCount: number;
    lastViolationMs: number;
    tier: RateLimiterTier;
    bannedUntilMs: number;
}

export interface RateLimitDecision {
    allowed: boolean;
    remainingTokens: number;
    retryAfterMs: number;
    tier: RateLimiterTier;
}

export class AdaptiveRateLimiter {
    private options: Required<RateLimiterOptions>;
    private buckets: Map<string, ClientBucketState> = new Map();

    constructor(options: RateLimiterOptions) {
        this.options = {
            capacity: Math.max(1, options.capacity),
            refillTokensPerSecond: Math.max(0.1, options.refillTokensPerSecond),
            violationWindowMs: options.violationWindowMs ?? 60000,
            throttleThresholdViolations: options.throttleThresholdViolations ?? 3,
            banThresholdViolations: options.banThresholdViolations ?? 10,
            banDurationMs: options.banDurationMs ?? 300000,
            now: options.now ?? (() => Date.now()),
        };
    }

    private getOrCreateBucket(key: string, now: number): ClientBucketState {
        let bucket = this.buckets.get(key);
        if (!bucket) {
            bucket = {
                tokens: this.options.capacity,
                lastRefillMs: now,
                violationsCount: 0,
                lastViolationMs: 0,
                tier: "NORMAL",
                bannedUntilMs: 0,
            };
            this.buckets.set(key, bucket);
        }
        return bucket;
    }

    /**
     * Replenishes tokens in the bucket according to elapsed time.
     */
    private refillTokens(bucket: ClientBucketState, now: number): void {
        const elapsedMs = Math.max(0, now - bucket.lastRefillMs);
        const tokensToAdd = (elapsedMs / 1000) * this.options.refillTokensPerSecond;

        // In THROTTLED tier, effective capacity and refill rate are halved
        const effectiveCapacity = bucket.tier === "THROTTLED" 
            ? Math.max(1, Math.floor(this.options.capacity / 2)) 
            : this.options.capacity;

        bucket.tokens = Math.min(effectiveCapacity, bucket.tokens + tokensToAdd);
        bucket.lastRefillMs = now;
    }

    /**
     * Checks rate limit and consumes the specified number of tokens.
     */
    public consume(key: string, cost = 1): RateLimitDecision {
        const now = this.options.now();
        const bucket = this.getOrCreateBucket(key, now);

        // Check active Ban status
        if (bucket.tier === "BANNED") {
            if (now < bucket.bannedUntilMs) {
                return {
                    allowed: false,
                    remainingTokens: 0,
                    retryAfterMs: bucket.bannedUntilMs - now,
                    tier: "BANNED",
                };
            }
            // Ban expired, downgrade to THROTTLED
            bucket.tier = "THROTTLED";
            bucket.violationsCount = this.options.throttleThresholdViolations;
            bucket.tokens = 1;
            bucket.lastRefillMs = now;
        }

        // Clean up expired violation history
        if (bucket.lastViolationMs > 0 && now - bucket.lastViolationMs > this.options.violationWindowMs) {
            bucket.violationsCount = 0;
            bucket.tier = "NORMAL";
        }

        this.refillTokens(bucket, now);

        if (bucket.tokens >= cost) {
            bucket.tokens -= cost;
            return {
                allowed: true,
                remainingTokens: Math.floor(bucket.tokens),
                retryAfterMs: 0,
                tier: bucket.tier,
            };
        }

        // Rate limit exceeded: Record violation
        bucket.violationsCount += 1;
        bucket.lastViolationMs = now;

        // Escalate penalty tier
        if (bucket.violationsCount >= this.options.banThresholdViolations) {
            bucket.tier = "BANNED";
            bucket.bannedUntilMs = now + this.options.banDurationMs;
            return {
                allowed: false,
                remainingTokens: 0,
                retryAfterMs: this.options.banDurationMs,
                tier: "BANNED",
            };
        } else if (bucket.violationsCount >= this.options.throttleThresholdViolations) {
            bucket.tier = "THROTTLED";
        }

        const missingTokens = cost - bucket.tokens;
        const retryAfterMs = Math.ceil((missingTokens / this.options.refillTokensPerSecond) * 1000);

        return {
            allowed: false,
            remainingTokens: Math.max(0, Math.floor(bucket.tokens)),
            retryAfterMs,
            tier: bucket.tier,
        };
    }

    /**
     * Purges inactive client buckets to prevent unbounded memory growth.
     */
    public purgeStale(maxIdleMs = 600000): number {
        const now = this.options.now();
        let purged = 0;

        for (const [key, bucket] of this.buckets.entries()) {
            if (now - bucket.lastRefillMs > maxIdleMs && bucket.tier !== "BANNED") {
                this.buckets.delete(key);
                purged++;
            }
        }

        return purged;
    }
}