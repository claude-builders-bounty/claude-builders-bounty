import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedCuckooFilter } from "./index.js";

describe("DistributedCuckooFilter Probabilistic Membership & Deletion", () => {
    it("inserts, verifies presence, and deletes items with zero false negatives", () => {
        const filter = new DistributedCuckooFilter(512, 4);

        const items = ["auth_token_alpha", "auth_token_beta", "auth_token_gamma"];
        for (const item of items) {
            assert.equal(filter.insert(item), true);
        }

        for (const item of items) {
            assert.equal(filter.contains(item), true);
        }

        assert.equal(filter.contains("non_existent_token"), false);

        // Delete beta
        assert.equal(filter.delete("auth_token_beta"), true);
        assert.equal(filter.contains("auth_token_beta"), false);
        assert.equal(filter.contains("auth_token_alpha"), true);
    });

    it("handles hundreds of elements with high load factor", () => {
        const filter = new DistributedCuckooFilter(256, 4);

        for (let i = 0; i < 300; i++) {
            filter.insert(`ip_addr_192_168_1_${i}`);
        }

        assert.ok(filter.size >= 290);
        assert.equal(filter.contains("ip_addr_192_168_1_50"), true);
    });

    it("defensively handles empty strings and invalid inputs", () => {
        const filter = new DistributedCuckooFilter();

        assert.equal(filter.insert(""), false);
        assert.equal(filter.insert(null as any), false);
        assert.equal(filter.contains(""), false);
        assert.equal(filter.delete(""), false);
    });
});