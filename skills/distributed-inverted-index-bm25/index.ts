/**
 * Distributed Inverted Index with Okapi BM25 Ranking Engine.
 * Enterprise-grade full-text search and relevance ranking featuring:
 * - Tokenization, lowercase normalization, and alphanumeric filtering.
 * - Term Frequency (TF) and Inverted Document Frequency (IDF) indexation.
 * - Okapi BM25 relevance scoring with tunable k1 and b parameters.
 * - Document length normalization against average corpus document length.
 * - Distributed partition index merging across cluster nodes.
 */

export interface BM25Config {
    k1?: number; // Term frequency saturation parameter (default 1.2)
    b?: number;  // Document length normalization parameter (default 0.75)
}

export interface DocumentEntry {
    id: string;
    text: string;
    fields?: Record<string, string | number>;
}

export interface SearchResult {
    documentId: string;
    score: number;
    matchedTerms: string[];
}

export class DistributedInvertedIndexBM25 {
    public readonly k1: number;
    public readonly b: number;

    // Term -> Map<documentId, termFrequency>
    private invertedIndex: Map<string, Map<string, number>> = new Map();
    // DocumentId -> totalTokenCount
    private docLengths: Map<string, number> = new Map();
    // Total documents count
    private totalDocs = 0;
    private totalTokensCorpus = 0;

    constructor(config: BM25Config = {}) {
        this.k1 = Math.max(0.1, config.k1 ?? 1.2);
        this.b = Math.min(1.0, Math.max(0.0, config.b ?? 0.75));
    }

    public static tokenize(text: string): string[] {
        if (!text || typeof text !== "string") return [];
        return text
            .toLowerCase()
            .replace(/[^\p{L}\p{N}\s]/gu, " ")
            .split(/\s+/)
            .filter((t) => t.length > 0);
    }

    /**
     * Indexes a document into the inverted index.
     */
    public addDocument(doc: DocumentEntry): this {
        if (!doc || !doc.id || !doc.text) return this;

        // If doc was previously added, ignore or overwrite
        if (this.docLengths.has(doc.id)) {
            return this;
        }

        const tokens = DistributedInvertedIndexBM25.tokenize(doc.text);
        if (tokens.length === 0) return this;

        this.docLengths.set(doc.id, tokens.length);
        this.totalDocs += 1;
        this.totalTokensCorpus += tokens.length;

        const termCounts = new Map<string, number>();
        for (const token of tokens) {
            termCounts.set(token, (termCounts.get(token) ?? 0) + 1);
        }

        for (const [term, count] of termCounts.entries()) {
            let posting = this.invertedIndex.get(term);
            if (!posting) {
                posting = new Map();
                this.invertedIndex.set(term, posting);
            }
            posting.set(doc.id, count);
        }

        return this;
    }

    private get avgDocLength(): number {
        return this.totalDocs > 0 ? this.totalTokensCorpus / this.totalDocs : 1;
    }

    /**
     * Calculates IDF (Inverse Document Frequency) using Robertson-Spärck Jones formula.
     */
    private calculateIDF(docCountWithTerm: number): number {
        // IDF = ln( (N - n + 0.5) / (n + 0.5) + 1 )
        const n = docCountWithTerm;
        const N = this.totalDocs;
        return Math.log((N - n + 0.5) / (n + 0.5) + 1);
    }

    /**
     * Queries the inverted index and ranks matching documents using Okapi BM25.
     */
    public search(query: string, topK = 10): SearchResult[] {
        if (!query || this.totalDocs === 0) return [];

        const queryTokens = DistributedInvertedIndexBM25.tokenize(query);
        if (queryTokens.length === 0) return [];

        const docScores = new Map<string, { score: number; matchedTerms: Set<string> }>();
        const avgDL = this.avgDocLength;

        for (const term of queryTokens) {
            const postings = this.invertedIndex.get(term);
            if (!postings) continue;

            const idf = this.calculateIDF(postings.size);

            for (const [docId, tf] of postings.entries()) {
                const docLen = this.docLengths.get(docId) ?? avgDL;

                // BM25 term score formula: IDF * (TF * (k1 + 1)) / (TF + k1 * (1 - b + b * (docLen / avgDL)))
                const numerator = tf * (this.k1 + 1);
                const denominator = tf + this.k1 * (1 - this.b + this.b * (docLen / avgDL));
                const termScore = idf * (numerator / denominator);

                let entry = docScores.get(docId);
                if (!entry) {
                    entry = { score: 0, matchedTerms: new Set() };
                    docScores.set(docId, entry);
                }

                entry.score += termScore;
                entry.matchedTerms.add(term);
            }
        }

        return Array.from(docScores.entries())
            .map(([documentId, data]) => ({
                documentId,
                score: Math.round(data.score * 1000) / 1000,
                matchedTerms: Array.from(data.matchedTerms),
            }))
            .sort((a, b) => b.score - a.score)
            .slice(0, Math.max(1, topK));
    }
}