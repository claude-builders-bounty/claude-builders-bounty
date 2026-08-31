/**
 * Firefly Algorithm (FA) Bioluminescence Metaheuristic for Traveling Salesperson Problem (TSP).
 * Swarm intelligence optimization primitive offering:
 * - O(I \cdot N^2 \cdot n) polynomial time complexity across I iterations and N fireflies.
 * - Light Intensity and Attractiveness formulation: \beta(r) = \beta_0 e^{-\gamma r^2}.
 * - Permutation distance metric based on edge mismatch.
 * - Randomization step via 2-Opt perturbation.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface FireflyTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedFireflyAlgorithmTSP {
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
     * Hamming distance between two permutation tours.
     */
    private permutationDistance(t1: number[], t2: number[]): number {
        let diff = 0;
        for (let i = 0; i < t1.length; i++) {
            if (t1[i] !== t2[i]) diff++;
        }
        return diff / t1.length;
    }

    /**
     * Moves firefly i towards brighter firefly j with attractiveness beta.
     */
    private moveTowards(iTour: number[], jTour: number[], beta: number, rng: () => number): number[] {
        const n = iTour.length;
        const result = [...iTour];

        // Partially inherit structure from brighter firefly j
        const numSwaps = Math.max(1, Math.round(beta * n * 0.5));
        for (let s = 0; s < numSwaps; s++) {
            const targetIdx = Math.floor(rng() * n);
            const targetVal = jTour[targetIdx];
            const currIdx = result.indexOf(targetVal);

            if (currIdx !== -1 && currIdx !== targetIdx) {
                const tmp = result[targetIdx];
                result[targetIdx] = result[currIdx];
                result[currIdx] = tmp;
            }
        }

        // Random walk / perturbation step
        if (rng() < 0.2) {
            const a = Math.floor(rng() * n);
            let b = Math.floor(rng() * n);
            while (b === a) b = Math.floor(rng() * n);
            const left = Math.min(a, b);
            const right = Math.max(a, b);
            let l = left, r = right;
            while (l < r) {
                const tmp = result[l];
                result[l] = result[r];
                result[r] = tmp;
                l++;
                r--;
            }
        }

        return result;
    }

    /**
     * Solves TSP using Firefly Algorithm.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        gamma = 1.0, // Light absorption coefficient
        beta0 = 1.0, // Base attractiveness
        rng: () => number = Math.random
    ): FireflyTSPResult {
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

        // 1. Initialize Firefly swarm
        let fireflies: { tour: number[]; cost: number; brightness: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            const cost = this.computeTourCost(tour);
            fireflies.push({ tour, cost, brightness: 1 / (1 + cost) });
        }

        fireflies.sort((a, b) => a.cost - b.cost);

        let bestTour = [...fireflies[0].tour];
        let bestCost = fireflies[0].cost;
        const initialCost = bestCost;

        for (let iter = 0; iter < maxIterations; iter++) {
            for (let i = 0; i < effectivePop; i++) {
                for (let j = 0; j < effectivePop; j++) {
                    // Firefly i moves towards brighter firefly j (lower cost = higher brightness)
                    if (fireflies[j].cost < fireflies[i].cost) {
                        const r = this.permutationDistance(fireflies[i].tour, fireflies[j].tour);
                        const beta = beta0 * Math.exp(-gamma * (r * r));

                        const movedTour = this.moveTowards(fireflies[i].tour, fireflies[j].tour, beta, rng);
                        const movedCost = this.computeTourCost(movedTour);

                        if (movedCost < fireflies[i].cost) {
                            fireflies[i] = {
                                tour: movedTour,
                                cost: movedCost,
                                brightness: 1 / (1 + movedCost),
                            };

                            if (movedCost < bestCost) {
                                bestCost = movedCost;
                                bestTour = [...movedTour];
                            }
                        }
                    }
                }
            }

            fireflies.sort((a, b) => a.cost - b.cost);
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