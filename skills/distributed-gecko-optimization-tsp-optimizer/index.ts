/**
 * Gecko Optimization Algorithm (GOA) Dynamic Wall Climbing & Nocturnal Insect Pounce Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired lizard adhesive locomotion search primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N virtual geckos.
 * - 2-Phase ecological foraging: Phase 1 (Nocturnal insect attraction near light source) and Phase 2 (Adhesive wall pounce exploitation).
 * - Dynamic radius reduction R * (1 - t/T).
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface GOATSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedGeckoOptimizationTSPOptimizer {
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
     * Gecko movement crossover towards target tour.
     */
    private geckoMove(tour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
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
     * Solves TSP using Gecko Optimization Algorithm.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        R = 0.2,
        rng: () => number = Math.random
    ): GOATSPResult {
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

        // 1. Initialize Gecko population
        let geckos: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            geckos.push({ tour, cost: this.computeTourCost(tour) });
        }

        geckos.sort((a, b) => a.cost - b.cost);

        let bestGecko = { ...geckos[0] };
        const initialCost = bestGecko.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            const lightSource = bestGecko.tour;

            // Phase 1: Nocturnal Insect Attraction near Light Source
            for (let i = 0; i < effectivePop; i++) {
                let newTour: number[];
                if (geckos[i].cost > bestGecko.cost) {
                    newTour = this.geckoMove(geckos[i].tour, lightSource, 0.65, rng);
                } else {
                    const randomClimb = this.generateRandomPermutation(n, rng);
                    newTour = this.geckoMove(geckos[i].tour, randomClimb, 0.35, rng);
                }

                const newCost = this.computeTourCost(newTour);
                if (newCost < geckos[i].cost) {
                    geckos[i] = { tour: newTour, cost: newCost };
                    if (newCost < bestGecko.cost) {
                        bestGecko = { tour: newTour, cost: newCost };
                    }
                }
            }

            // Phase 2: Adhesive Setae Wall Pounce Exploitation
            const radius = R * (1 - iter / maxIterations);
            for (let i = 0; i < effectivePop; i++) {
                const step1 = this.geckoMove(geckos[i].tour, bestGecko.tour, 0.55 + radius, rng);

                // 2-opt local search refinement
                if (rng() < 0.2) {
                    const l = Math.floor(rng() * n);
                    let rp = Math.floor(rng() * n);
                    while (rp === l) rp = Math.floor(rng() * n);
                    const left = Math.min(l, rp);
                    const right = Math.max(l, rp);
                    let lp = left, rpp = right;
                    while (lp < rpp) {
                        const tmp = step1[lp];
                        step1[lp] = step1[rpp];
                        step1[rpp] = tmp;
                        lp++;
                        rpp--;
                    }
                }

                const newCost = this.computeTourCost(step1);
                if (newCost < geckos[i].cost) {
                    geckos[i] = { tour: step1, cost: newCost };
                    if (newCost < bestGecko.cost) {
                        bestGecko = { tour: step1, cost: newCost };
                    }
                }
            }

            geckos.sort((a, b) => a.cost - b.cost);
        }

        const finalTour: string[] = [...bestGecko.tour.map(i => this.points[i].id), this.points[bestGecko.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: bestGecko.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}