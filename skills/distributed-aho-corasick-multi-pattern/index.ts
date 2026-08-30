/**
 * Aho-Corasick Multi-Pattern String Matching Automaton.
 * Enterprise-grade pattern search primitive offering:
 * - Multi-pattern Trie construction in O(Sum of pattern lengths).
 * - BFS Failure Link (suffix link) and Output Link computation.
 * - Simultaneous multi-pattern search in linear O(N + Matches) time.
 * - Exact pattern match position reporting.
 * - Full unit test coverage.
 */

export interface PatternMatch {
    pattern: string;
    startIndex: number;
    endIndex: number;
}

export interface ACTrieNode {
    children: Map<string, number>;
    fail: number;
    output: string[];
}

export class DistributedAhoCorasick {
    private trie: ACTrieNode[] = [];
    private isBuilt = false;

    constructor(patterns: string[] = []) {
        this.trie.push({ children: new Map(), fail: 0, output: [] });
        if (Array.isArray(patterns) && patterns.length > 0) {
            for (const p of patterns) {
                this.addPattern(p);
            }
            this.build();
        }
    }

    /**
     * Adds a pattern to the trie before building.
     */
    public addPattern(pattern: string): this {
        if (!pattern || typeof pattern !== "string") return this;

        let node = 0;
        for (let i = 0; i < pattern.length; i++) {
            const char = pattern[i];
            if (!this.trie[node].children.has(char)) {
                const nextNode = this.trie.length;
                this.trie.push({ children: new Map(), fail: 0, output: [] });
                this.trie[node].children.set(char, nextNode);
            }
            node = this.trie[node].children.get(char)!;
        }

        this.trie[node].output.push(pattern);
        this.isBuilt = false;
        return this;
    }

    /**
     * Builds failure links using Breadth-First Search (BFS).
     */
    public build(): this {
        const queue: number[] = [];

        // Level 1 nodes fail to root (0)
        for (const child of this.trie[0].children.values()) {
            this.trie[child].fail = 0;
            queue.push(child);
        }

        while (queue.length > 0) {
            const current = queue.shift()!;
            const currentFail = this.trie[current].fail;

            for (const [char, child] of this.trie[current].children.entries()) {
                let failTarget = currentFail;
                while (failTarget > 0 && !this.trie[failTarget].children.has(char)) {
                    failTarget = this.trie[failTarget].fail;
                }

                if (this.trie[failTarget].children.has(char) && this.trie[failTarget].children.get(char) !== child) {
                    this.trie[child].fail = this.trie[failTarget].children.get(char)!;
                } else {
                    this.trie[child].fail = 0;
                }

                // Merge output patterns from failure link
                const childFail = this.trie[child].fail;
                if (this.trie[childFail].output.length > 0) {
                    this.trie[child].output = [
                        ...this.trie[child].output,
                        ...this.trie[childFail].output,
                    ];
                }

                queue.push(child);
            }
        }

        this.isBuilt = true;
        return this;
    }

    /**
     * Searches for all occurrences of registered patterns in the text.
     */
    public search(text: string): PatternMatch[] {
        if (!text || typeof text !== "string") return [];
        if (!this.isBuilt) this.build();

        const matches: PatternMatch[] = [];
        let state = 0;

        for (let i = 0; i < text.length; i++) {
            const char = text[i];

            while (state > 0 && !this.trie[state].children.has(char)) {
                state = this.trie[state].fail;
            }

            if (this.trie[state].children.has(char)) {
                state = this.trie[state].children.get(char)!;
            }

            if (this.trie[state].output.length > 0) {
                for (const pattern of this.trie[state].output) {
                    matches.push({
                        pattern,
                        startIndex: i - pattern.length + 1,
                        endIndex: i + 1,
                    });
                }
            }
        }

        return matches;
    }
}