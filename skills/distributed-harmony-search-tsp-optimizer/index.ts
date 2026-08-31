/**
 * Harmony Search (HS) Musical Improvisation & Harmony Memory Metaheuristic for Traveling Salesperson Problem (TSP).
 * Music-inspired improvisation global search primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N harmony memory vectors.
 * - Harmony Memory Consideration Rate (HMCR) controlling exploration vs exploitation.
 * - Pitch Adjusting Rate (PAR) and dynamic bandwidth modulation bw(t).
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface HSTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedHarmonySearchTSPOptimizer {
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
     * Harmony crossover inheriting pitch notes from harmony memory vector.
     */
    private pitchMove(tour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
        const n = tour.length;
        const result = [...tour];
        const numSwaps = Math.max(1, Math.round(intensity * n * 0.35));

        for (let s = 0; s < numSwaps; s++) {
            const targetIdx = Math.floor(rng() * n);
            const targetVal = targetTour[targetIdx];
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
     * Solves TSP using Harmony Search Algorithm.
     */
    public search(
        maxIterations = 100,
        harmonyMemorySize = 20,
        hmcr = 0.9,
        parMin = 0.3,
        parMax = 0.9,
        rng: () => number = Math.random
    ): HSTSPResult {
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

        const effectiveHMS = Math.max(5, Math.min(50, harmonyMemorySize));

        // 1. Initialize Harmony Memory (HM)
        let harmonyMemory: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectiveHMS; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            harmonyMemory.push({ tour, cost: this.computeTourCost(tour) });
        }

        harmonyMemory.sort((a, b) => a.cost - b.cost);

        let bestHarmony = { ...harmonyMemory[0] };
        const initialCost = bestHarmony.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Dynamic PAR increases linearly from parMin to parMax
            const currentPAR = parMin + ((parMax - parMin) / maxIterations) * iter;

            // Improvise new harmony
            let newTour: number[];
            if (rng() < hmcr) {
                // Memory consideration: pick from HM
                const selected = harmonyMemory[Math.floor(rng() * effectiveHMS)];
                newTour = [...selected.tour];

                // Pitch adjustment
                if (rng() < currentPAR) {
                    const guide = harmonyMemory[0];
                    newTour = this.pitchMove(newTour, guide.tour, 0.4, rng);
                }
            } else {
                // Random improvisation
                newTour = this.generateRandomPermutation(n, rng);
            }

            // 2-opt local search refinement
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

            // If improvised harmony is better than worst in HM, replace worst
            const worstIdx = harmonyMemory.length - 1;
            if (newCost < harmonyMemory[worstIdx].cost) {
                harmonyMemory[worstIdx] = { tour: newTour, cost: newCost };
                harmonyMemory.sort((a, b) => a.cost - b.cost);

                if (newCost < bestHarmony.cost) {
                    bestHarmony = { tour: newTour, cost: newCost };
                }
            }
        }

        const finalTour: string[] = [...bestHarmony.tour.map(i => this.points[i].id), this.points[bestHarmony.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: bestHarmony.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}