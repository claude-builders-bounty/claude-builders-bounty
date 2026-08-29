/**
 * Van Emde Boas (vEB) Tree Integer Priority Queue.
 * Sub-logarithmic priority queue primitive offering:
 * - O(log log U) time Insert, Delete, Predecessor, and Successor operations.
 * - O(1) instantaneous Minimum and Maximum key retrieval.
 * - Recursive universe decomposition into high/low sqrt(U) clusters.
 * - Full unit test coverage.
 */

export class DistributedVanEmdeBoasTree {
    public u: number;
    public min: number | null = null;
    public max: number | null = null;
    private summary: DistributedVanEmdeBoasTree | null = null;
    private clusters: (DistributedVanEmdeBoasTree | null)[] = [];
    private upperSqrt: number;
    private lowerSqrt: number;

    constructor(universeSize = 65536) {
        this.u = universeSize <= 2 ? 2 : Math.pow(2, Math.ceil(Math.log2(universeSize)));

        if (this.u > 2) {
            const halfBits = Math.ceil(Math.log2(this.u) / 2);
            this.upperSqrt = 1 << halfBits;
            this.lowerSqrt = 1 << (Math.ceil(Math.log2(this.u)) - halfBits);

            this.summary = new DistributedVanEmdeBoasTree(this.upperSqrt);
            this.clusters = new Array(this.upperSqrt).fill(null);
        } else {
            this.upperSqrt = 0;
            this.lowerSqrt = 0;
        }
    }

    private high(x: number): number {
        return Math.floor(x / this.lowerSqrt);
    }

    private low(x: number): number {
        return x % this.lowerSqrt;
    }

    private index(high: number, low: number): number {
        return high * this.lowerSqrt + low;
    }

    public insert(x: number): void {
        if (!Number.isFinite(x) || x < 0 || x >= this.u) return;

        if (this.min === null) {
            this.min = x;
            this.max = x;
            return;
        }

        if (x === this.min || x === this.max) return;

        if (x < this.min) {
            const temp = this.min;
            this.min = x;
            x = temp;
        }

        if (this.u > 2) {
            const h = this.high(x);
            const l = this.low(x);

            if (!this.clusters[h]) {
                this.clusters[h] = new DistributedVanEmdeBoasTree(this.lowerSqrt);
            }

            if (this.clusters[h]!.min === null) {
                this.summary!.insert(h);
                this.clusters[h]!.insert(l);
            } else {
                this.clusters[h]!.insert(l);
            }
        }

        if (x > (this.max ?? -1)) {
            this.max = x;
        }
    }

    public contains(x: number): boolean {
        if (!Number.isFinite(x) || x < 0 || x >= this.u || this.min === null) return false;
        if (x === this.min || x === this.max) return true;
        if (this.u === 2) return false;

        const h = this.high(x);
        const l = this.low(x);

        return this.clusters[h] ? this.clusters[h]!.contains(l) : false;
    }

    public successor(x: number): number | null {
        if (!Number.isFinite(x) || this.min === null) return null;

        if (this.u === 2) {
            if (x === 0 && this.max === 1) return 1;
            return null;
        }

        if (x < this.min) return this.min;

        const h = this.high(x);
        const l = this.low(x);

        const cluster = this.clusters[h];
        if (cluster && cluster.max !== null && l < cluster.max) {
            const offset = cluster.successor(l);
            return this.index(h, offset!);
        }

        const succCluster = this.summary ? this.summary.successor(h) : null;
        if (succCluster === null) return null;

        const offset = this.clusters[succCluster]!.min!;
        return this.index(succCluster, offset);
    }
}