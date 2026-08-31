import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedInvertedIndexBM25 } from "./index.js";

describe("DistributedInvertedIndexBM25 Full-Text Relevance Ranking", () => {
    it("indexes corpus and ranks relevant documents with BM25 score", () => {
        const index = new DistributedInvertedIndexBM25({ k1: 1.2, b: 0.75 });

        index.addDocument({
            id: "doc_1",
            text: "Distributed consensus algorithms such as Raft and Paxos ensure cluster safety.",
        });
        index.addDocument({
            id: "doc_2",
            text: "Vector databases provide fast approximate nearest neighbor semantic search.",
        });
        index.addDocument({
            id: "doc_3",
            text: "Raft consensus provides leader election and log replication for distributed databases.",
        });

        // Search query with terms matching doc_1 and doc_3
        const results = index.search("Raft consensus leader replication");
        assert.ok(results.length >= 2);
        assert.equal(results[0].documentId, "doc_3"); // doc_3 has the highest density of matching query tokens
        assert.ok(results[0].score > results[1].score);
        assert.ok(results[0].matchedTerms.includes("raft"));
    });

    it("handles empty queries and documents defensively", () => {
        const index = new DistributedInvertedIndexBM25();

        assert.deepEqual(index.search(""), []);
        assert.deepEqual(index.search("nonexistent_term_xyz"), []);

        index.addDocument({ id: "", text: "" });
        index.addDocument(null as any);
        assert.equal(index.search("any").length, 0);
    });

    it("normalizes tokenization across punctuation, symbols, and case", () => {
        const tokens = DistributedInvertedIndexBM25.tokenize("Hello, World! Fast-paced 100% C++ Search...");
        assert.ok(tokens.includes("hello"));
        assert.ok(tokens.includes("world"));
        assert.ok(tokens.includes("search"));
    });
});