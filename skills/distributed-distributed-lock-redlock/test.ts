import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedRedlock, LockInstanceNode } from "./index.js";

function createMockNode(nodeId: string): LockInstanceNode & { store: Map<string, { val: string; expires: number }> } {
    const store = new Map<string, { val: string; expires: number }>();
    return {
        nodeId,
        store,
        acquire(resource, token, ttlMs) {
            const existing = store.get(resource);
            if (existing && existing.expires > Date.now()) return false;
            store.set(resource, { val: token, expires: Date.now() + ttlMs });
            return true;
        },
        release(resource, token) {
            const existing = store.get(resource);
            if (existing && existing.val === token) {
                store.delete(resource);
                return true;
            }
            return false;
        },
        extend(resource, token, ttlMs) {
            const existing = store.get(resource);
            if (existing && existing.val === token) {
                existing.expires = Date.now() + ttlMs;
                return true;
            }
            return false;
        },
    };
}

describe("DistributedRedlock Quorum, Fencing Tokens & Lifecycle", () => {
    it("successfully acquires lock across 3-node cluster and generates monotonic fencing token", async () => {
        const n1 = createMockNode("node_1");
        const n2 = createMockNode("node_2");
        const n3 = createMockNode("node_3");

        const redlock = new DistributedRedlock([n1, n2, n3]);
        const lock1 = await redlock.acquire("db_user_100", 5000);

        assert.ok(lock1 !== null);
        assert.equal(lock1.resource, "db_user_100");
        assert.ok(lock1.fencingToken > 0);
        assert.ok(lock1.validityMs > 4500);

        // Cannot acquire concurrently by another caller
        const lock2 = await redlock.acquire("db_user_100", 5000);
        assert.equal(lock2, null);

        // Release lock
        const released = await redlock.release(lock1);
        assert.equal(released, true);

        // Can acquire again after release with incremented fencing token
        const lock3 = await redlock.acquire("db_user_100", 5000);
        assert.ok(lock3 !== null);
        assert.ok(lock3.fencingToken > lock1.fencingToken);
    });

    it("fails and rolls back cleanly when quorum cannot be reached", async () => {
        const n1 = createMockNode("node_1");
        const n2: LockInstanceNode = {
            nodeId: "node_2_offline",
            acquire: () => false,
            release: () => false,
            extend: () => false,
        };
        const n3: LockInstanceNode = {
            nodeId: "node_3_offline",
            acquire: () => false,
            release: () => false,
            extend: () => false,
        };

        const redlock = new DistributedRedlock([n1, n2, n3], { retryCount: 0 });
        const lock = await redlock.acquire("critical_resource", 5000);

        assert.equal(lock, null);
        // Node 1 should be compensated/released
        assert.equal(n1.store.has("critical_resource"), false);
    });

    it("extends active lock lease safely", async () => {
        const n1 = createMockNode("node_1");
        const n2 = createMockNode("node_2");
        const n3 = createMockNode("node_3");

        const redlock = new DistributedRedlock([n1, n2, n3]);
        const lock = await redlock.acquire("stream_channel_01", 3000);
        assert.ok(lock !== null);

        const extended = await redlock.extend(lock, 6000);
        assert.ok(extended !== null);
        assert.ok(extended.validityMs > 5000);
    });

    it("guards defensively against invalid inputs and empty node lists", async () => {
        assert.throws(() => new DistributedRedlock([]), /requires at least 1 node/);

        const n1 = createMockNode("node_1");
        const redlock = new DistributedRedlock([n1]);

        assert.equal(await redlock.acquire("", 1000), null);
        assert.equal(await redlock.acquire("res", NaN as any), null);
        assert.equal(await redlock.acquire("res", -500), null);
        assert.equal(await redlock.release(null as any), false);
    });
});