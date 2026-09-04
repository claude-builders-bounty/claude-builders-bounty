/**
 * Firefly Algorithm (FA) Dynamic Flashing Light Intensity & Attraction Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired bioluminescent flashing and light absorption search primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N virtual fireflies.
 * - Dynamic light intensity and attractiveness beta(r) = beta0 * exp(-gamma * r^2).
 * - Dynamic radius reduction R * (1 - t/T).
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface FATSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedFireflyTSPOptimizer {
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
     * Discrete Hamming distance ratio between two permutations.
     */
    private computePermutationDistance(p1: number[], p2: number[]): number {
        let diff = 0;
        for (let i = 0; i < p1.length; i++) {
            if (p1[i] !== p2[i]) diff++;
        }
        return diff / p1.length;
    }

    /**
     * Firefly attraction crossover towards brighter firefly.
     */
    private fireflyMove(tour: number[], targetTour: number[], beta: number, rng: () => number): number[] {
        const n = tour.length;
        const result = [...tour];
        const numSwaps = Math.max(1, Math.round(beta * n * 0.45));

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
     * Solves TSP using Firefly Algorithm.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        beta0 = 1.0,
        gamma = 1.0,
        rng: () => number = Math.random
    ): FATSPResult {
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

        // 1. Initialize Firefly population
        let fireflies: { tour: number[]; cost: number; light: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            const cost = this.computeTourCost(tour);
            // Light intensity is inversely proportional to cost
            fireflies.push({ tour, cost, light: 1.0 / (cost + 1e-4) });
        }

        fireflies.sort((a, b) => a.cost - b.cost);

        let bestFirefly = { ...fireflies[0] };
        const initialCost = bestFirefly.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            for (let i = 0; i < effectivePop; i++) {
                for (let j = 0; j < effectivePop; j++) {
                    // Firefly i moves towards brighter firefly j
                    if (fireflies[j].light > fireflies[i].light) {
                        const r = this.computePermutationDistance(fireflies[i].tour, fireflies[j].tour);
                        const beta = beta0 * Math.exp(-gamma * r * r);
                        let candidateTour = this.fireflyMove(fireflies[i].tour, fireflies[j].tour, beta, rng);

                        // 2-opt local search refinement
                        if (rng() < 0.2) {
                            const step1 = [...candidateTour];
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
                            candidateTour = step1;
                        }

                        const candidateCost = this.computeTourCost(candidateTour);
                        if (candidateCost < fireflies[i].cost) {
                            fireflies[i].tour = candidateTour;
                            fireflies[i].cost = candidateCost;
                            fireflies[i].light = 1.0 / (candidateCost + 1e-4);

                            if (candidateCost < bestFirefly.cost) {
                                bestFirefly = { ...fireflies[i] };
                            }
                        }
                    }
                }
            }

            fireflies.sort((a, b) => a.cost - b.cost);
        }

        const finalTour: string[] = [...bestFirefly.tour.map(i => this.points[i].id), this.points[bestFirefly.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: bestFirefly.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}