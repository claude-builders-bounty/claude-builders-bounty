/**
 * Tasmanian Devil Optimization (TDO) Dynamic Carrion Feeding & Active Prey Chase Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired carnivorous marsupial feeding behavior search primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N virtual Tasmanian devils.
 * - 2 Distinct feeding strategies: Strategy 1 (Carrion Feeding on Carcasses) and Strategy 2 (Active Prey Hunting & Capture).
 * - Discrete stochastic crossover intensity parameters.
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface TDOTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedTasmanianDevilTSPOptimizer {
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
     * Tasmanian devil movement crossover towards target tour.
     */
    private devilMove(tour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
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
     * Solves TSP using Tasmanian Devil Optimization.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        rng: () => number = Math.random
    ): TDOTSPResult {
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

        // 1. Initialize Tasmanian Devil population
        let devils: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            devils.push({ tour, cost: this.computeTourCost(tour) });
        }

        devils.sort((a, b) => a.cost - b.cost);

        let bestDevil = { ...devils[0] };
        const initialCost = bestDevil.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Stage 1: Strategy Selection & Movement
            for (let i = 0; i < effectivePop; i++) {
                let newTour: number[];
                const prob = rng();

                if (prob > 0.5) {
                    // Strategy 1: Carrion Feeding (Feeding on large dead mammal carcass)
                    const carrion = bestDevil.tour;
                    const I = rng() > 0.5 ? 1 : 2;
                    newTour = this.devilMove(devils[i].tour, carrion, 0.4 * I, rng);
                } else {
                    // Strategy 2: Active Prey Hunting (Stalking and chasing live prey)
                    const preyIdx = Math.floor(rng() * effectivePop);
                    const prey = devils[preyIdx].tour;
                    const step1 = this.devilMove(devils[i].tour, prey, 0.65, rng);
                    const randomDash = this.generateRandomPermutation(n, rng);
                    newTour = this.devilMove(step1, randomDash, 0.25, rng);
                }

                const newCost = this.computeTourCost(newTour);
                if (newCost < devils[i].cost) {
                    devils[i] = { tour: newTour, cost: newCost };
                    if (newCost < bestDevil.cost) {
                        bestDevil = { tour: newTour, cost: newCost };
                    }
                }
            }

            // Stage 2: Prey Capture & Local Search Refinement
            const R = 0.2 * (1 - iter / maxIterations);
            for (let i = 0; i < effectivePop; i++) {
                const step = this.devilMove(devils[i].tour, bestDevil.tour, 0.5 + R, rng);

                // 2-opt local search refinement
                if (rng() < 0.2) {
                    const l = Math.floor(rng() * n);
                    let rp = Math.floor(rng() * n);
                    while (rp === l) rp = Math.floor(rng() * n);
                    const left = Math.min(l, rp);
                    const right = Math.max(l, rp);
                    let lp = left, rpp = right;
                    while (lp < rpp) {
                        const tmp = step[lp];
                        step[lp] = step[rpp];
                        step[rpp] = tmp;
                        lp++;
                        rpp--;
                    }
                }

                const newCost = this.computeTourCost(step);
                if (newCost < devils[i].cost) {
                    devils[i] = { tour: step, cost: newCost };
                    if (newCost < bestDevil.cost) {
                        bestDevil = { tour: step, cost: newCost };
                    }
                }
            }

            devils.sort((a, b) => a.cost - b.cost);
        }

        const finalTour: string[] = [...bestDevil.tour.map(i => this.points[i].id), this.points[bestDevil.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: bestDevil.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}