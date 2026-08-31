import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedVanEmdeBoasTree } from "./index.js";

describe("DistributedVanEmdeBoasTree Sub-Logarithmic Priority Operations", () => {
    it("inserts keys and maintains O(1) minimum and maximum bounds", () => {
        const veb = new DistributedVanEmdeBoasTree(256);

        veb.insert(42);
        veb.insert(10);
        veb.insert(100);
        veb.insert(5);

        assert.equal(veb.min, 5);
        assert.equal(veb.max, 100);
        assert.equal(veb.contains(42), true);
        assert.equal(veb.contains(99), false);
    });

    it("computes exact integer successors in sub-logarithmic time", () => {
        const veb = new DistributedVanEmdeBoasTree(256);

        [10, 20, 30, 70, 150].forEach((k) => veb.insert(k));

        assert.equal(veb.successor(10), 20);
        assert.equal(veb.successor(25), 30);
        assert.equal(veb.successor(30), 70);
        assert.equal(veb.successor(70), 150);
        assert.equal(veb.successor(150), null);
    });

    it("defensively handles out-of-range keys and empty queries", () => {
        const veb = new DistributedVanEmdeBoasTree(16);

        veb.insert(-5);
        veb.insert(999);
        assert.equal(veb.min, null);

        assert.equal(veb.contains(NaN), false);
        assert.equal(veb.successor(10), null);
    });
});