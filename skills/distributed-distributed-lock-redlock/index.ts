/**
 * Distributed Redlock Mutual Exclusion Algorithm with Fencing Tokens.
 * Enterprise-grade multi-node distributed locking primitive featuring:
 * - Quorum Acquisition: Requires consensus across >= floor(N/2) + 1 independent nodes.
 * - Clock Drift Factor: Compensates for clock skew (validity = TTL - elapsed - drift).
 * - Monotonic Fencing Tokens: Generates strictly incrementing sequence numbers for downstream resource fencing.
 * - Automatic Compensation: Releases acquired locks across all nodes if quorum or validity time fails.
 * - Safe Heartbeat Lease Extension: Extends lock TTL safely if lease has not expired.
 */

export interface LockInstanceNode {
    nodeId: string;
    acquire: (resource: string, token: string, ttlMs: number) => Promise<boolean> | boolean;
    release: (resource: string, token: string) => Promise<boolean> | boolean;
    extend: (resource: string, token: string, ttlMs: number) => Promise<boolean> | boolean;
}

export interface RedlockLock {
    resource: string;
    value: string;
    fencingToken: number;
    validityMs: number;
    expiresAtEpochMs: number;
}

export interface RedlockConfig {
    driftFactor?: number;      // Clock drift factor, default 0.01 (1%)
    retryCount?: number;       // Number of acquisition retries
    retryDelayMs?: number;     // Delay between retries
    now?: () => number;        // Injectable clock
}

export class DistributedRedlock {
    private nodes: LockInstanceNode[] = [];
    private driftFactor: number;
    private retryCount: number;
    private retryDelayMs: number;
    private now: () => number;
    private static globalFencingSequence = 0;

    constructor(nodes: LockInstanceNode[], config: RedlockConfig = {}) {
        if (!nodes || nodes.length === 0) {
            throw new Error("DistributedRedlock requires at least 1 node instance.");
        }
        this.nodes = [...nodes];
        this.driftFactor = Math.max(0, config.driftFactor ?? 0.01);
        this.retryCount = Math.max(0, config.retryCount ?? 3);
        this.retryDelayMs = Math.max(10, config.retryDelayMs ?? 50);
        this.now = config.now ?? (() => Date.now());
    }

    private get quorum(): number {
        return Math.floor(this.nodes.length / 2) + 1;
    }

    /**
     * Attempts to acquire the distributed lock across the node cluster.
     */
    public async acquire(resource: string, ttlMs: number): Promise<RedlockLock | null> {
        if (!resource || !Number.isFinite(ttlMs) || ttlMs <= 0) {
            return null;
        }

        const lockValue = `lock_${Math.random().toString(36).substring(2)}_${this.now()}`;
        const quorum = this.quorum;

        for (let attempt = 0; attempt <= this.retryCount; attempt++) {
            const startTime = this.now();
            let acquiredCount = 0;

            for (const node of this.nodes) {
                try {
                    const success = await Promise.resolve(node.acquire(resource, lockValue, ttlMs));
                    if (success) acquiredCount++;
                } catch {
                    // Node communication failure counts as non-acquisition
                }
            }

            const elapsed = this.now() - startTime;
            const drift = Math.floor(ttlMs * this.driftFactor) + 2;
            const validityMs = ttlMs - elapsed - drift;

            if (acquiredCount >= quorum && validityMs > 0) {
                DistributedRedlock.globalFencingSequence += 1;
                return {
                    resource,
                    value: lockValue,
                    fencingToken: DistributedRedlock.globalFencingSequence,
                    validityMs,
                    expiresAtEpochMs: this.now() + validityMs,
                };
            }

            // Quorum or validity failed: Compensate and release across all nodes
            await this.releaseNodes(resource, lockValue);

            if (attempt < this.retryCount) {
                const jitter = Math.floor(Math.random() * (this.retryDelayMs / 2));
                await new Promise((res) => setTimeout(res, this.retryDelayMs + jitter));
            }
        }

        return null;
    }

    /**
     * Releases the distributed lock across all nodes.
     */
    public async release(lock: RedlockLock): Promise<boolean> {
        if (!lock || !lock.resource || !lock.value) {
            return false;
        }
        return this.releaseNodes(lock.resource, lock.value);
    }

    private async releaseNodes(resource: string, value: string): Promise<boolean> {
        let releaseCount = 0;
        for (const node of this.nodes) {
            try {
                const released = await Promise.resolve(node.release(resource, value));
                if (released) releaseCount++;
            } catch {
                // Ignore node release errors
            }
        }
        return releaseCount >= this.quorum;
    }

    /**
     * Extends an active lock lease before it expires.
     */
    public async extend(lock: RedlockLock, additionalTtlMs: number): Promise<RedlockLock | null> {
        if (!lock || !lock.resource || !lock.value || !Number.isFinite(additionalTtlMs) || additionalTtlMs <= 0) {
            return null;
        }

        if (this.now() >= lock.expiresAtEpochMs) {
            return null; // Already expired
        }

        const startTime = this.now();
        let extendedCount = 0;

        for (const node of this.nodes) {
            try {
                const success = await Promise.resolve(node.extend(lock.resource, lock.value, additionalTtlMs));
                if (success) extendedCount++;
            } catch {}
        }

        const elapsed = this.now() - startTime;
        const drift = Math.floor(additionalTtlMs * this.driftFactor) + 2;
        const validityMs = additionalTtlMs - elapsed - drift;

        if (extendedCount >= this.quorum && validityMs > 0) {
            lock.validityMs = validityMs;
            lock.expiresAtEpochMs = this.now() + validityMs;
            return lock;
        }

        return null;
    }
}