import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedConsistentHashBoundedLoads } from "./index.js";

describe("DistributedConsistentHashBoundedLoads Load Balancing", () => {
    it("distributes keys without exceeding bounded load capacity cap", () => {
        // 4 nodes, epsilon 0.25 -> maximum 125% average load
        const ch = new DistributedConsistentHashBoundedLoads({ vnodesPerNode: 30, epsilon: 0.25 });
        ch.addNode("node_A").addNode("node_B").addNode("node_C").addNode("node_D");

        // Insert 200 keys (average 50 keys per node, cap = ceil(1.25 * 50) = 63 keys max)
        for (let i = 0; i < 200; i++) {
            ch.assignKey(`user_cache_key_${i}`);
        }

        for (const node of ["node_A", "node_B", "node_C", "node_D"]) {
            const load = ch.getNodeLoad(node);
            assert.ok(load <= 65, `Node ${node} exceeded capacity cap with load ${load}`);
            assert.ok(load >= 35, `Node ${node} was severely underloaded with load ${load}`);
        }
    });

    it("reassigns keys smoothly when a node departs", () => {
        const ch = new DistributedConsistentHashBoundedLoads();
        ch.addNode("server_1").addNode("server_2").addNode("server_3");

        for (let i = 0; i < 60; i++) {
            ch.assignKey(`session_${i}`);
        }

        assert.equal(ch.getNodeLoad("server_1") > 0, true);

        // Remove server_1
        ch.removeNode("server_1");
        assert.equal(ch.getNodeLoad("server_1"), 0);

        // Remaining servers took over the keys
        const totalRemaining = ch.getNodeLoad("server_2") + ch.getNodeLoad("server_3");
        assert.equal(totalRemaining, 60);
    });

    it("defensively handles empty nodes and null keys", () => {
        const ch = new DistributedConsistentHashBoundedLoads();
        assert.equal(ch.assignKey("key_1"), null);
        assert.equal(ch.getCapacityLimit(100), 0);
    });
});