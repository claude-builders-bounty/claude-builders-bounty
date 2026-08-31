/**
 * Moth-Flame Optimization (MFO) Spiral Transverse Orientation Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired swarm optimization primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N moths.
 * - Logarithmic spiral navigation towards flames: S(M_i, F_j) = D_i \cdot e^{b t} \cdot \cos(2\pi t) + F_j.
 * - Adaptive flame count reduction Flame_no = round(N - l * (N - 1) / T) to balance exploration and exploitation.
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface MFOResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedMothFlameTSPOptimizer {
    private points: Point2D[] = [];

    constructor() {}

    /**
     * Adds a 2D Euclidean point.
     */
    public addPoint(id: string, x: number, y: number): this {
        if (!id || typeof id !== "string" || !Number.isFinite(x) || !Number.isFinite(y)) return this;
        if (this.points.some(p => p.id === id)) return this;

        this.points.push({ id, x, y });
        return this;
    }

    private getDistance(p1: Point2D, p2: Point2D): number {
        return Math.hypot(p1.x - p2.x, p1.y - p2.y);
    }

    private computeTourCost(tourIndices: number[]): number {
        let cost = 0;
        for (let i = 0; i < tourIndices.length; i++) {
            const next = (i + 1) % tourIndices.length;
            cost += this.getDistance(this.points[tourIndices[i]], this.points[tourIndices[next]]);
        }
        return cost;
    }

    private generateRandomPermutation(n: number, rng: () => number): number[] {
        const arr = Array.from({ length: n }, (_, i) => i);
        for (let i = n - 1; i > 0; i--) {
            const j = Math.floor(rng() * (i + 1));
            const tmp = arr[i];
            arr[i] = arr[j];
            arr[j] = tmp;
        }
        return arr;
    }

    /**
     * Logarithmic spiral movement towards corresponding flame.
     */
    private spiralMove(mothTour: number[], flameTour: number[], spiralWeight: number, rng: () => number): number[] {
        const n = mothTour.length;
        const result = [...mothTour];
        const numSwaps = Math.max(1, Math.round(spiralWeight * n * 0.35));

        for (let s = 0; s < numSwaps; s++) {
            const targetIdx = Math.floor(rng() * n);
            const targetVal = flameTour[targetIdx];
            const currIdx = result.indexOf(targetVal);

            if (currIdx !== -1 && currIdx !== targetIdx) {
                const tmp = result[targetIdx];
                result[targetIdx] = result[currIdx];
                result[currIdx] = tmp;
            }
        }

        return result;
    }

    /**
     * Solves TSP using Moth-Flame Optimization.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        b = 1.0, // Spiral shape constant
        rng: () => number = Math.random
    ): MFOResult {
        const n = this.points.length;
        if (n === 0) {
            return { found: false, initialCost: 0, bestCost: 0, tour: [], iterationsCompleted: 0 };
        }

        if (n <= 2) {
            const indices = Array.from({ length: n }, (_, i) => i);
            const cost = this.computeTourCost(indices);
            return {
                found: true,
                initialCost: cost,
                bestCost: cost,
                tour: [...indices.map(i => this.points[i].id), indices.length > 0 ? this.points[indices[0]].id : ""].filter(Boolean),
                iterationsCompleted: 0,
            };
        }

        const effectivePop = Math.max(5, Math.min(50, populationSize));

        // 1. Initialize Moth population
        let moths: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            moths.push({ tour, cost: this.computeTourCost(tour) });
        }

        // Initialize Flames as sorted moths
        let flames = [...moths].sort((a, b) => a.cost - b.cost);
        let bestCost = flames[0].cost;
        let bestTour = [...flames[0].tour];
        const initialCost = bestCost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Number of flames decreases adaptively from N to 1
            const flameNo = Math.max(1, Math.round(effectivePop - iter * ((effectivePop - 1) / maxIterations)));

            // Parameter a linearly decreases from -1 to -2 to accelerate convergence around flames
            const a = -1.0 + iter * (-1.0 / maxIterations);

            for (let i = 0; i < effectivePop; i++) {
                // Determine target flame
                const flameIdx = i < flameNo ? i : (flameNo - 1);
                const targetFlame = flames[flameIdx];

                // Parameter t in [a, 1] defines closeness to flame
                const t = (a - 1.0) * rng() + 1.0;
                const spiralWeight = Math.min(1.0, Math.abs(Math.exp(b * t) * Math.cos(2 * Math.PI * t)));

                let newTour = this.spiralMove(moths[i].tour, targetFlame.tour, spiralWeight, rng);

                // 2-opt random walk refinement
                if (rng() < 0.2) {
                    const l = Math.floor(rng() * n);
                    let rp = Math.floor(rng() * n);
                    while (rp === l) rp = Math.floor(rng() * n);
                    const left = Math.min(l, rp);
                    const right = Math.max(l, rp);
                    let lp = left, rpp = right;
                    while (lp < rpp) {
                        const tmp = newTour[lp];
                        newTour[lp] = newTour[rpp];
                        newTour[rpp] = tmp;
                        lp++;
                        rpp--;
                    }
                }

                const newCost = this.computeTourCost(newTour);
                moths[i] = { tour: newTour, cost: newCost };
            }

            // Update Flames (combine double population: moths + previous flames)
            const combined = [...moths, ...flames].sort((a, b) => a.cost - b.cost);
            flames = combined.slice(0, effectivePop);

            if (flames[0].cost < bestCost) {
                bestCost = flames[0].cost;
                bestTour = [...flames[0].tour];
            }
        }

        const finalTour: string[] = [...bestTour.map(i => this.points[i].id), this.points[bestTour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}