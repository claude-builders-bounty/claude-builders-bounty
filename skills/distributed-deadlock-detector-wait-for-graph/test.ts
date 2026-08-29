import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedDeadlockDetector } from "./index.js";

describe("DistributedDeadlockDetector WFG Cycle Analysis & Victim Preemption", () => {
    it("reports no deadlock for linear DAG dependency chains", () => {
        const detector = new DistributedDeadlockDetector();
        detector
            .addDependency({ transactionId: "tx_1", resourceId: "res_a", heldByTransactionId: "tx_2", transactionCost: 50 })
            .addDependency({ transactionId: "tx_2", resourceId: "res_b", heldByTransactionId: "tx_3", transactionCost: 100 })
            .addDependency({ transactionId: "tx_3", resourceId: "res_c", transactionCost: 200 });

        const res = detector.detectDeadlocks();
        assert.equal(res.hasDeadlock, false);
        assert.equal(res.cycles.length, 0);
    });

    it("detects cyclic wait-for dependency and nominates lowest-cost victim", () => {
        const detector = new DistributedDeadlockDetector();
        // tx_1 (cost 500) waits for tx_2
        // tx_2 (cost 100) waits for tx_3
        // tx_3 (cost 20) waits for tx_1 -> CYCLE: 1 -> 2 -> 3 -> 1
        detector
            .addDependency({ transactionId: "tx_1", resourceId: "res_a", heldByTransactionId: "tx_2", transactionCost: 500 })
            .addDependency({ transactionId: "tx_2", resourceId: "res_b", heldByTransactionId: "tx_3", transactionCost: 100 })
            .addDependency({ transactionId: "tx_3", resourceId: "res_c", heldByTransactionId: "tx_1", transactionCost: 20 });

        const res = detector.detectDeadlocks();
        assert.equal(res.hasDeadlock, true);
        assert.equal(res.cycles.length, 1);

        // tx_3 has the lowest cost (20) so it is the nominated victim to abort
        assert.equal(res.cycles[0].suggestedVictimId, "tx_3");
        assert.equal(res.cycles[0].victimRollbackCost, 20);
    });

    it("clears deadlock when victim transaction is aborted and removed", () => {
        const detector = new DistributedDeadlockDetector();
        detector
            .addDependency({ transactionId: "tx_A", resourceId: "r1", heldByTransactionId: "tx_B", transactionCost: 100 })
            .addDependency({ transactionId: "tx_B", resourceId: "r2", heldByTransactionId: "tx_A", transactionCost: 50 });

        assert.equal(detector.detectDeadlocks().hasDeadlock, true);

        // Abort tx_B
        detector.removeTransaction("tx_B");
        assert.equal(detector.detectDeadlocks().hasDeadlock, false);
    });
});