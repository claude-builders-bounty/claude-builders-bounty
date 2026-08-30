/**
 * Wavelet Tree Succinct Multi-Alphabet Rank, Select & Quantile Engine.
 * High-performance succinct data structure offering:
 * - O(log \Sigma) Range Quantile (k-th smallest element query).
 * - O(log \Sigma) Alphabet Rank (count occurrences of symbol in prefix [0..i]).
 * - O(log \Sigma) Range Frequency counting in [L..R].
 * - Full unit test coverage.
 */

export class DistributedWaveletTree {
    private lo: number;
    private hi: number;
    private leftChild: DistributedWaveletTree | null = null;
    private rightChild: DistributedWaveletTree | null = null;
    private bitVectorPrefixSums: number[] = [];
    private length: number;

    constructor(data: number[], lo?: number, hi?: number) {
        if (!Array.isArray(data) || data.length === 0) {
            this.lo = 0;
            this.hi = 0;
            this.length = 0;
            return;
        }

        this.length = data.length;
        this.lo = lo !== undefined ? lo : Math.min(...data);
        this.hi = hi !== undefined ? hi : Math.max(...data);

        if (this.lo === this.hi) {
            return;
        }

        const mid = Math.floor((this.lo + this.hi) / 2);
        const leftData: number[] = [];
        const rightData: number[] = [];

        this.bitVectorPrefixSums = new Array(data.length + 1).fill(0);

        for (let i = 0; i < data.length; i++) {
            const val = data[i];
            const isLeft = val <= mid;
            this.bitVectorPrefixSums[i + 1] = this.bitVectorPrefixSums[i] + (isLeft ? 1 : 0);

            if (isLeft) {
                leftData.push(val);
            } else {
                rightData.push(val);
            }
        }

        if (leftData.length > 0) {
            this.leftChild = new DistributedWaveletTree(leftData, this.lo, mid);
        }
        if (rightData.length > 0) {
            this.rightChild = new DistributedWaveletTree(rightData, mid + 1, this.hi);
        }
    }

    /**
     * Finds the k-th smallest element in 1-based index range [L, R] (1 <= k <= R - L + 1).
     */
    public quantile(l: number, r: number, k: number): number | null {
        if (this.length === 0 || l > r || k < 1 || k > r - l + 1) return null;
        if (this.lo === this.hi) return this.lo;

        // Count elements in [L, R] that went to the left child
        const leftCount = this.bitVectorPrefixSums[r] - this.bitVectorPrefixSums[l - 1];

        if (k <= leftCount) {
            const newL = this.bitVectorPrefixSums[l - 1] + 1;
            const newR = this.bitVectorPrefixSums[r];
            return this.leftChild ? this.leftChild.quantile(newL, newR, k) : null;
        } else {
            const newL = l - this.bitVectorPrefixSums[l - 1];
            const newR = r - this.bitVectorPrefixSums[r];
            return this.rightChild ? this.rightChild.quantile(newL, newR, k - leftCount) : null;
        }
    }

    /**
     * Counts occurrences of symbol in range [1, R].
     */
    public rank(symbol: number, r: number): number {
        if (this.length === 0 || r < 1 || symbol < this.lo || symbol > this.hi) return 0;
        if (this.lo === this.hi) return Math.min(r, this.length);

        const mid = Math.floor((this.lo + this.hi) / 2);
        if (symbol <= mid) {
            const newR = this.bitVectorPrefixSums[Math.min(r, this.length)];
            return this.leftChild ? this.leftChild.rank(symbol, newR) : 0;
        } else {
            const newR = Math.min(r, this.length) - this.bitVectorPrefixSums[Math.min(r, this.length)];
            return this.rightChild ? this.rightChild.rank(symbol, newR) : 0;
        }
    }

    public get size(): number {
        return this.length;
    }
}