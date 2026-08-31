import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedAdaptiveRadixTree } from "./index.js";

describe("DistributedAdaptiveRadixTree Prefix & Range Queries", () => {
    it("inserts, searches, and deletes keys in the ART index", () => {
        const art = new DistributedAdaptiveRadixTree<number>();

        art.insert("user:100:profile", 100);
        art.insert("user:100:orders", 5);
        art.insert("user:200:profile", 200);

        assert.equal(art.size, 3);
        assert.equal(art.search("user:100:profile"), 100);
        assert.equal(art.search("user:999"), null);

        const deleted = art.delete("user:100:orders");
        assert.equal(deleted, true);
        assert.equal(art.size, 2);
        assert.equal(art.search("user:100:orders"), null);
    });

    it("performs fast prefix search and range queries", () => {
        const art = new DistributedAdaptiveRadixTree<string>();

        art.insert("config.db.host", "localhost");
        art.insert("config.db.port", "5432");
        art.insert("config.db.user", "postgres");
        art.insert("config.cache.redis", "redis://localhost:6379");

        const dbConfigs = art.prefixSearch("config.db.");
        assert.equal(dbConfigs.length, 3);
        assert.equal(dbConfigs[0].key, "config.db.host");

        const rangeResults = art.range("config.cache.", "config.db.p");
        const keys = rangeResults.map((r) => r.key);
        assert.ok(keys.includes("config.cache.redis"));
        assert.ok(keys.includes("config.db.host"));
        assert.ok(!keys.includes("config.db.user")); // "user" > "p"
    });

    it("defensively handles empty keys and null lookups", () => {
        const art = new DistributedAdaptiveRadixTree();

        assert.equal(art.search(""), null);
        assert.equal(art.search(null as any), null);
        assert.equal(art.delete(""), false);
        assert.deepEqual(art.prefixSearch(""), []);

        art.insert("", "val");
        assert.equal(art.size, 0);
    });
});