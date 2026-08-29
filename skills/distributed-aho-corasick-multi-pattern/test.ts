import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedAhoCorasick } from "./index.js";

describe("DistributedAhoCorasick Multi-Pattern Linear Search", () => {
    it("finds all overlapping and distinct keywords simultaneously in linear time", () => {
        const ac = new DistributedAhoCorasick(["he", "she", "his", "hers"]);

        const matches = ac.search("ushers_and_hisses");
        const found = matches.map((m) => `${m.pattern}@${m.startIndex}`);

        assert.ok(found.includes("she@1"));
        assert.ok(found.includes("he@2"));
        assert.ok(found.includes("hers@2"));
        assert.ok(found.includes("his@11"));
    });

    it("matches cybersecurity indicators and SQL injection vectors", () => {
        const waf = new DistributedAhoCorasick(["union select", "drop table", "exec xp_", "<script>"]);

        const payload = decodeURIComponent("GET /search?q=1%20UNION%20SELECT%20*%20FROM%20users");
        const matches = waf.search(payload.toLowerCase());

        assert.equal(matches.length, 1);
        assert.equal(matches[0].pattern, "union select");
    });

    it("defensively handles empty strings and patterns", () => {
        const ac = new DistributedAhoCorasick();

        assert.deepEqual(ac.search(""), []);
        assert.deepEqual(ac.search(null as any), []);

        ac.addPattern("");
        assert.deepEqual(ac.search("some text"), []);
    });
});