import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedBurstTrie } from "./index.js";

describe("DistributedBurstTrie Cache-Conscious String Index", () => {
    it("inserts, searches, and deletes keys in the burst trie", () => {
        const trie = new DistributedBurstTrie<number>(8);

        trie.insert("algorithm:raft", 1);
        trie.insert("algorithm:paxos", 2);
        trie.insert("algorithm:zab", 3);

        assert.equal(trie.size, 3);
        assert.equal(trie.search("algorithm:raft"), 1);
        assert.equal(trie.search("algorithm:unknown"), null);

        assert.equal(trie.delete("algorithm:paxos"), true);
        assert.equal(trie.size, 2);
    });

    it("performs fast prefix scans across indexed keys", () => {
        const trie = new DistributedBurstTrie<string>();

        trie.insert("net.ipv4.tcp_syncookies", "1");
        trie.insert("net.ipv4.ip_forward", "0");
        trie.insert("net.ipv6.conf.all.disable_ipv6", "1");

        const ipv4Entries = trie.prefixSearch("net.ipv4.");
        assert.equal(ipv4Entries.length, 2);
        assert.equal(ipv4Entries[0].key, "net.ipv4.ip_forward");
    });

    it("defensively handles empty strings and invalid inputs", () => {
        const trie = new DistributedBurstTrie();

        assert.equal(trie.search(""), null);
        assert.equal(trie.search(null as any), null);
        assert.equal(trie.delete(""), false);
        assert.deepEqual(trie.prefixSearch(""), []);

        trie.insert("", "val" as any);
        assert.equal(trie.size, 0);
    });
});