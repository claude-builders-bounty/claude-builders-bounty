/**
 * Distributed HyperLogLog (HLL) Probabilistic Cardinality Estimator.
 * Features:
 * - Sub-linear memory unique element estimation with configurable precision p (4 <= p <= 16).
 * - Murmur/FNV hash distribution with leading zero rank estimation.
 * - Harmonic mean register aggregation with standard alpha correction factors.
 * - Small range linear counting correction for near-zero bias.
 * - Lossless register array merge for distributed cluster aggregation.
 */

export class DistributedHyperLogLog {
    public readonly p: number; // Precision bits (e.g. 4 to 14)
    public readonly m: number; // Number of registers 2^p
    private readonly registers: Uint8Array;
    private readonly alphaMM: number;

    constructor(precision = 8) {
        this.p = Math.min(14, Math.max(4, precision));
        this.m = 1 << this.p;
        this.registers = new Uint8Array(this.m);

        // Precalculate alpha_m * m^2
        let alpha = 0.7213 / (1 + 1.079 / this.m);
        if (this.m === 16) alpha = 0.673;
        else if (this.m === 32) alpha = 0.697;
        else if (this.m === 64) alpha = 0.709;

        this.alphaMM = alpha * this.m * this.m;
    }

    /**
     * MurmurHash3 32-bit implementation for balanced bit dispersion.
     */
    private murmur3(key: string, seed = 0): number {
        let h1 = seed >>> 0;
        const c1 = 0xcc9e2d51;
        const c2 = 0x1b873593;

        for (let i = 0; i < key.length; i++) {
            let k1 = key.charCodeAt(i);
            k1 = Math.imul(k1, c1);
            k1 = (k1 << 15) | (k1 >>> 17);
            k1 = Math.imul(k1, c2);

            h1 ^= k1;
            h1 = (h1 << 13) | (h1 >>> 19);
            h1 = (Math.imul(h1, 5) + 0xe6546b64) >>> 0;
        }

        h1 ^= key.length;
        h1 ^= h1 >>> 16;
        h1 = Math.imul(h1, 0x85ebca6b);
        h1 ^= h1 >>> 13;
        h1 = Math.imul(h1, 0xc2b2ae35);
        h1 ^= h1 >>> 16;

        return h1 >>> 0;
    }

    /**
     * Adds an element to the HLL estimator.
     */
    public add(element: string): this {
        const hash = this.murmur3(element);
        const registerIndex = hash >>> (32 - this.p);
        const remainingBits = (hash << this.p) >>> 0;

        // Rank of the first 1-bit: clz32 + 1
        const rank = remainingBits === 0 ? (32 - this.p + 1) : (Math.clz32(remainingBits) + 1);

        if (rank > this.registers[registerIndex]) {
            this.registers[registerIndex] = rank;
        }
        return this;
    }

    /**
     * Estimates the distinct count (cardinality).
     */
    public count(): number {
        let harmonicSum = 0;
        let zeroRegisters = 0;

        for (let i = 0; i < this.m; i++) {
            const val = this.registers[i];
            harmonicSum += Math.pow(2, -val);
            if (val === 0) zeroRegisters++;
        }

        let estimate = this.alphaMM / harmonicSum;

        // Small range correction (LinearCounting)
        if (estimate <= 2.5 * this.m && zeroRegisters > 0) {
            estimate = this.m * Math.log(this.m / zeroRegisters);
        }

        return Math.round(estimate);
    }

    /**
     * Merges another HLL register state into this instance.
     */
    public merge(other: DistributedHyperLogLog): this {
        if (this.p !== other.p) {
            throw new Error("Cannot merge HyperLogLog instances with different precisions.");
        }
        for (let i = 0; i < this.m; i++) {
            this.registers[i] = Math.max(this.registers[i], other.registers[i]);
        }
        return this;
    }
}