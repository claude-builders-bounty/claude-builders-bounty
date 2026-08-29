import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedConsistentHashRing } from "./index.js";

describe("DistributedConsistentHashRing Key Routing & Replica Lists", () => {
    it("routes keys deterministically to available nodes", () => {
        const ring = new DistributedConsistentHashRing({ vnodesPerNode: 20 });
        ring.addNode("node_A").addNode("node_B").addNode("node_C");

        const targetNode1 = ring.getNode("user_session_9921");
        const targetNode2 = ring.getNode("user_session_9921");

        assert.ok(targetNode1);
        assert.equal(targetNode1, targetNode2); // Deterministic
    });

    it("returns N distinct physical nodes in replica preference list", () => {
        const ring = new DistributedConsistentHashRing({ vnodesPerNode: 30 });
        ring.addNode("node_1").addNode("node_2").addNode("node_3").addNode("node_4");

        const replicas = ring.getPreferenceList("shard_partition_key", 3);
        assert.equal(replicas.length, 3);
        // All replica nodes must be unique
        const uniqueSet = new Set(replicas);
        assert.equal(uniqueSet.size, 3);
    });

    it("handles node removal smoothly without routing to deleted nodes", () => {
        const ring = new DistributedConsistentHashRing({ vnodesPerNode: 10 });
        ring.addNode("cache_1").addNode("cache_2");

        ring.removeNode("cache_1");
        const target = ring.getNode("some_data_key");
        assert.equal(target, "cache_2");
    });
});