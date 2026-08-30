import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedTwoPhaseCommitCoordinator, TwoPhaseParticipant } from "./index.js";

describe("DistributedTwoPhaseCommitCoordinator 2PC Protocol", () => {
    it("successfully commits when all participants vote to prepare", async () => {
        const coordinator = new DistributedTwoPhaseCommitCoordinator();

        let db1Committed = false;
        let db2Committed = false;

        const db1: TwoPhaseParticipant = {
            participantId: "postgres_primary",
            prepare: () => true,
            commit: () => { db1Committed = true; },
            abort: () => {},
        };

        const db2: TwoPhaseParticipant = {
            participantId: "redis_cache",
            prepare: () => true,
            commit: () => { db2Committed = true; },
            abort: () => {},
        };

        coordinator.registerParticipant(db1).registerParticipant(db2);

        const result = await coordinator.executeTransaction("tx_1001");
        assert.equal(result.status, "COMMITTED");
        assert.equal(db1Committed, true);
        assert.equal(db2Committed, true);
        assert.ok(result.phaseHistory.some(p => p.phase === "COMMITTED"));
    });

    it("aborts and rollbacks all participants if any single participant votes abort", async () => {
        const coordinator = new DistributedTwoPhaseCommitCoordinator();

        let db1Aborted = false;
        let db2Aborted = false;

        const db1: TwoPhaseParticipant = {
            participantId: "node_alpha",
            prepare: () => true,
            commit: () => {},
            abort: () => { db1Aborted = true; },
        };

        const db2: TwoPhaseParticipant = {
            participantId: "node_beta",
            prepare: () => false, // VOTE_ABORT
            commit: () => {},
            abort: () => { db2Aborted = true; },
        };

        coordinator.registerParticipant(db1).registerParticipant(db2);

        const result = await coordinator.executeTransaction("tx_1002");
        assert.equal(result.status, "ABORTED");
        assert.equal(db1Aborted, true);
        assert.equal(db2Aborted, true);
        assert.ok(result.error?.includes("voted VOTE_ABORT"));
    });
});