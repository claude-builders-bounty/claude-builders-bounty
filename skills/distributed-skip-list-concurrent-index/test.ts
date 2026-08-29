import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedSkipList } from "./index.js";

describe("DistributedSkipList Probabilistic Index & Range Queries", () => {
    it("inserts, searches, updates, and deletes ordered keys", () => {
        const sl = new DistributedSkipList<number, string>();

        sl.insert(10, "ten").insert(5, "five").insert(20, "twenty").insert(15, "fifteen");

        assert.equal(sl.size, 4);
        assert.equal(sl.search(15), "fifteen");
        assert.equal(sl.search(100), null);

        // Update existing key
        sl.insert(10, "ten_updated");
        assert.equal(sl.search(10), "ten_updated");
        assert.equal(sl.size, 4);

        // Delete key
        const deleted = sl.delete(5);
        assert.equal(deleted, true);
        assert.equal(sl.size, 3);
        assert.equal(sl.search(5), null);
    });

    it("performs ordered range queries between minKey and maxKey", () => {
        const sl = new DistributedSkipList<number, string>();

        const numbers = [50, 10, 80, 25, 30, 95, 40, 70];
        for (const n of numbers) {
            sl.insert(n, `val_${n}`);
        }

        const rangeResult = sl.range(25, 75);
        const returnedKeys = rangeResult.map((r) => r.key);

        assert.deepEqual(returnedKeys, [25, 30, 40, 50, 70]);
    });

    it("defensively handles nulls and empty list searches", () => {
        const sl = new DistributedSkipList<string, string>();

        assert.equal(sl.search("nonexistent"), null);
        assert.equal(sl.delete("nonexistent"), false);
        assert.deepEqual(sl.range("a", "z"), []);

        sl.insert(null as any, "val");
        assert.equal(sl.size, 0);
    });
});