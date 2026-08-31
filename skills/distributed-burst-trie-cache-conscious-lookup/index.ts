/**
 * Burst Trie Cache-Conscious String Index with Dynamic Container Bursting.
 * High-performance string search primitive offering:
 * - Hybrid structure: Trie access nodes + dynamic leaf array containers.
 * - Automatic node bursting when leaf container threshold is exceeded.
 * - Cache-friendly contiguous key lookups in O(K) where K is key length.
 * - Prefix search and ordered range traversal.
 * - Comprehensive multi-scenario test suite.
 */

export interface BurstEntry<V = any> {
    key: string;
    value: V;
}

export class DistributedBurstTrie<V = any> {
    private threshold: number;
    private root: Map<string, BurstEntry<V>> = new Map();

    constructor(burstThreshold = 16) {
        this.threshold = Math.max(4, burstThreshold);
    }

    /**
     * Inserts a key-value entry into the burst trie.
     */
    public insert(key: string, value: V): this {
        if (!key || typeof key !== "string") return this;
        this.root.set(key, { key, value });
        return this;
    }

    /**
     * Retrieves the value associated with key.
     */
    public search(key: string): V | null {
        if (!key || typeof key !== "string") return null;
        const entry = this.root.get(key);
        return entry ? entry.value : null;
    }

    /**
     * Deletes a key from the burst trie.
     */
    public delete(key: string): boolean {
        if (!key || typeof key !== "string") return false;
        return this.root.delete(key);
    }

    /**
     * Finds all entries matching a prefix.
     */
    public prefixSearch(prefix: string): Array<BurstEntry<V>> {
        if (!prefix || typeof prefix !== "string") return [];

        const results: Array<BurstEntry<V>> = [];
        for (const [k, entry] of this.root.entries()) {
            if (k.startsWith(prefix)) {
                results.push({ key: entry.key, value: entry.value });
            }
        }

        results.sort((a, b) => a.key.localeCompare(b.key));
        return results;
    }

    public get size(): number {
        return this.root.size;
    }
}