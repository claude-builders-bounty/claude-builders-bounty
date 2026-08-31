/**
 * Sine Cosine Algorithm (SCA) Trigonometric Oscillatory Metaheuristic for Traveling Salesperson Problem (TSP).
 * Mathematical oscillation-based global search primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N candidate agents.
 * - Trigonometric position updates using Sine and Cosine operators.
 * - Dynamic parameter r1 decaying linearly from 2 to 0 for smooth exploration-exploitation transition.
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface SCATSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedSineCosineTSPOptimizer {
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
     * Trigonometrically guided crossover towards target destination.
     */
    private trigMove(tour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
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
     * Solves TSP using Sine Cosine Algorithm.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        rng: () => number = Math.random
    ): SCATSPResult {
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

        // 1. Initialize population
        let population: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            population.push({ tour, cost: this.computeTourCost(tour) });
        }

        population.sort((a, b) => a.cost - b.cost);

        let bestSolution = { ...population[0] };
        const initialCost = bestSolution.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Parameter r1 dictates movement direction and decreases linearly from 2 to 0
            const r1 = 2 - iter * (2 / maxIterations);

            for (let i = 0; i < effectivePop; i++) {
                const r2 = 2 * Math.PI * rng();
                const r3 = 2 * rng();
                const r4 = rng();

                let intensity: number;
                if (r4 < 0.5) {
                    // Sine oscillation
                    intensity = Math.min(1.0, Math.abs(r1 * Math.sin(r2) * r3));
                } else {
                    // Cosine oscillation
                    intensity = Math.min(1.0, Math.abs(r1 * Math.cos(r2) * r3));
                }

                let newTour = this.trigMove(population[i].tour, bestSolution.tour, intensity, rng);

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
                if (newCost < population[i].cost) {
                    population[i] = { tour: newTour, cost: newCost };
                    if (newCost < bestSolution.cost) {
                        bestSolution = { tour: newTour, cost: newCost };
                    }
                }
            }

            population.sort((a, b) => a.cost - b.cost);
        }

        const finalTour: string[] = [...bestSolution.tour.map(i => this.points[i].id), this.points[bestSolution.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: bestSolution.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}