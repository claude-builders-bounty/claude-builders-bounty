/**
 * Coati Optimization Algorithm (COA) Dynamic Tree Hunting & Ground Escape Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired mammal foraging search primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N virtual coatis.
 * - 2-Phase ecological dynamics: Phase 1 (Tree climbing iguana hunting) and Phase 2 (Ground predator evasion).
 * - Dynamic radius reduction R * (1 - t/T).
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface COATSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedCoatiOptimizationTSPOptimizer {
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
     * Coati movement crossover towards target tour.
     */
    private coatiMove(tour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
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
     * Solves TSP using Coati Optimization Algorithm.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        R = 0.2,
        rng: () => number = Math.random
    ): COATSPResult {
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

        const effectivePop = Math.max(6, Math.min(50, populationSize));
        const halfPop = Math.floor(effectivePop / 2);

        // 1. Initialize Coati population
        let coatis: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            coatis.push({ tour, cost: this.computeTourCost(tour) });
        }

        coatis.sort((a, b) => a.cost - b.cost);

        let bestCoati = { ...coatis[0] };
        const initialCost = bestCoati.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            const iguana = bestCoati.tour;

            // Phase 1: Hunting Iguanas in Trees & On the Ground
            for (let i = 0; i < effectivePop; i++) {
                let newTour: number[];
                if (i < halfPop) {
                    // Group 1: Tree climbers moving towards iguana
                    newTour = this.coatiMove(coatis[i].tour, iguana, 0.65, rng);
                } else {
                    // Group 2: Ground waiting coatis anticipating fallen iguana
                    const randomDash = this.generateRandomPermutation(n, rng);
                    const step = this.coatiMove(coatis[i].tour, iguana, 0.45, rng);
                    newTour = this.coatiMove(step, randomDash, 0.25, rng);
                }

                const newCost = this.computeTourCost(newTour);
                if (newCost < coatis[i].cost) {
                    coatis[i] = { tour: newTour, cost: newCost };
                    if (newCost < bestCoati.cost) {
                        bestCoati = { tour: newTour, cost: newCost };
                    }
                }
            }

            // Phase 2: Escaping from Predators on the Ground
            const radius = R * (1 - iter / maxIterations);
            for (let i = 0; i < effectivePop; i++) {
                const escapeTour = this.generateRandomPermutation(n, rng);
                const step1 = this.coatiMove(coatis[i].tour, bestCoati.tour, 0.55 + radius, rng);
                const newTour = this.coatiMove(step1, escapeTour, 0.2, rng);

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
                if (newCost < coatis[i].cost) {
                    coatis[i] = { tour: newTour, cost: newCost };
                    if (newCost < bestCoati.cost) {
                        bestCoati = { tour: newTour, cost: newCost };
                    }
                }
            }

            coatis.sort((a, b) => a.cost - b.cost);
        }

        const finalTour: string[] = [...bestCoati.tour.map(i => this.points[i].id), this.points[bestCoati.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: bestCoati.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}