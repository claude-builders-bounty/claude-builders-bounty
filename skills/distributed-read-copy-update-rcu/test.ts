import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { ReadCopyUpdateContainer } from "./index.js";

describe("ReadCopyUpdateContainer Lockless RCU Synchronization", () => {
    it("allows lockless readers to access published data without blocking updates", () => {
        interface Config {
            host: string;
            port: number;
        }

        const rcu = new ReadCopyUpdateContainer<Config>({ host: "127.0.0.1", port: 8080 });

        // Reader 1 takes snapshot
        const r1Data = rcu.rcuReadLock("reader_1");
        assert.equal(r1Data.port, 8080);

        // Writer updates pointer
        rcu.update((curr) => ({ ...curr, port: 9090 }));

        // Reader 1 still sees consistent old data (isolation)
        assert.equal(r1Data.port, 8080);

        // Reader 2 gets updated pointer
        const r2Data = rcu.rcuReadLock("reader_2");
        assert.equal(r2Data.port, 9090);

        rcu.rcuReadUnlock("reader_1");
        rcu.rcuReadUnlock("reader_2");
    });

    it("delays memory reclamation until reader exits grace period", () => {
        let reclaimedCount = 0;
        const rcu = new ReadCopyUpdateContainer<number[]>([1, 2, 3]);

        // Reader 1 enters RCU section
        rcu.rcuReadLock("reader_hold");

        // Update with reclamation callback
        rcu.update((arr) => [...arr, 4], () => { reclaimedCount++; });

        // Grace period not complete because reader_hold is still active
        assert.equal(reclaimedCount, 0);

        // Reader exits
        rcu.rcuReadUnlock("reader_hold");

        // Memory reclaimed
        assert.equal(reclaimedCount, 1);
    });
});