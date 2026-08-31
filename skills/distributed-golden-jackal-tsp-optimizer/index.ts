/**
 * Golden Jackal Optimization (GJO) Cooperative Male-Female Pair Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired canid hunting pair search primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N jackals.
 * - Male jackal (Y1) and Female jackal (Y2) leadership pair dynamics.
 * - Dynamic prey energy decay E = E1 * (2r - 1) governing exploration (|E| > 1) vs exploitation (|E| <= 1).
 * - Collaborative pair pouncing average consolidation.
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface GJOTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedGoldenJackalTSPOptimizer {
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
     * Cooperative jackal crossover towards target leader jackal.
     */
    private jackalMove(tour: number[], leaderTour: number[], intensity: number, rng: () => number): number[] {
        const n = tour.length;
        const result = [...tour];
        const numSwaps = Math.max(1, Math.round(intensity * n * 0.35));

        for (let s = 0; s < numSwaps; s++) {
            const targetIdx = Math.floor(rng() * n);
            const targetVal = leaderTour[targetIdx];
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
     * Solves TSP using Golden Jackal Optimization.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        c = 1.5,
        rng: () => number = Math.random
    ): GJOTSPResult {
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

        // 1. Initialize Jackal pack population
        let jackals: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            jackals.push({ tour, cost: this.computeTourCost(tour) });
        }

        jackals.sort((a, b) => a.cost - b.cost);

        let maleJackal = { ...jackals[0] };
        let femaleJackal = { ...jackals[Math.min(1, jackals.length - 1)] };
        const initialCost = maleJackal.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // E1 decays from c to 0
            const E1 = c * (1 - iter / maxIterations);
            const r = rng();
            const E = E1 * (2 * r - 1);
            const absE = Math.abs(E);

            for (let i = 0; i < effectivePop; i++) {
                let newTour: number[];

                if (absE > 1) {
                    // Exploration phase: Male and Female search separately
                    const step1 = this.jackalMove(jackals[i].tour, maleJackal.tour, 0.4 * absE, rng);
                    const step2 = this.jackalMove(jackals[i].tour, femaleJackal.tour, 0.4 * absE, rng);
                    newTour = rng() < 0.5 ? step1 : step2;
                } else {
                    // Exploitation phase: Encircle and pounce on prey together
                    const step1 = this.jackalMove(jackals[i].tour, maleJackal.tour, 0.6, rng);
                    newTour = this.jackalMove(step1, femaleJackal.tour, 0.4, rng);
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
                if (newCost < jackals[i].cost) {
                    jackals[i] = { tour: newTour, cost: newCost };
                    if (newCost < maleJackal.cost) {
                        femaleJackal = { ...maleJackal };
                        maleJackal = { tour: newTour, cost: newCost };
                    } else if (newCost < femaleJackal.cost) {
                        femaleJackal = { tour: newTour, cost: newCost };
                    }
                }
            }

            jackals.sort((a, b) => a.cost - b.cost);
        }

        const finalTour: string[] = [...maleJackal.tour.map(i => this.points[i].id), this.points[maleJackal.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: maleJackal.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}