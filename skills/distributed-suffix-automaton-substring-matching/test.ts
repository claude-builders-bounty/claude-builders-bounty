import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedSuffixAutomaton } from "./index.js";

describe("DistributedSuffixAutomaton Linear Substring & LCS Search", () => {
    it("builds automaton and checks substring containment in linear time", () => {
        const sam = new DistributedSuffixAutomaton("distributed_consensus_raft_algorithm");

        assert.equal(sam.contains("consensus"), true);
        assert.equal(sam.contains("raft"), true);
        assert.equal(sam.contains("algorithm"), true);
        assert.equal(sam.contains("paxos"), false);
    });

    it("computes Longest Common Substring (LCS) accurately", () => {
        const sam = new DistributedSuffixAutomaton("abcdef_cryptographic_zk_snark_proof_xyz");
        const query = "blockchain_zk_snark_verification_engine";

        const { lcs, length } = sam.longestCommonSubstring(query);
        assert.equal(lcs, "_zk_snark_");
        assert.equal(length, 10);
    });

    it("defensively handles empty strings and invalid inputs", () => {
        const sam = new DistributedSuffixAutomaton();

        assert.equal(sam.contains(""), false);
        assert.equal(sam.contains(null as any), false);
        assert.deepEqual(sam.longestCommonSubstring(""), { lcs: "", length: 0 });
    });
});