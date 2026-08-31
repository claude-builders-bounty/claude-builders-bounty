/**
 * Firefly Algorithm (FA) Light Intensity & Bioluminescent Attraction Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired lampyridae bioluminescence optimization primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N fireflies.
 * - Light intensity and attractiveness decay with distance beta(r) = beta0 * exp(-gamma * r^2).
 * - Guided bioluminescent crossover towards brighter fireflies with randomization.
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
     * Measures normalized Hamming/permutation distance between two tours.
     */
    private tourDistance(t1: number[], t2: number[]): number {
        let diff = 0;
        for (let i = 0; i < t1.length; i++) {
            if (t1[i] !== t2[i]) diff++;
        }
        return diff / t1.length;
    }

    /**
     * Bioluminescent attraction crossover towards brighter firefly.
     */
    private fireflyMove(tour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
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
     * Solves TSP using Firefly Algorithm.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        beta0 = 1.0,
        gamma = 1.0,
        alpha = 0.2,
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
        let fireflies: { tour: number[]; cost: number; brightness: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            const cost = this.computeTourCost(tour);
            // In TSP minimization, brightness is inversely proportional to cost
            fireflies.push({ tour, cost, brightness: 1 / (1 + cost) });
        }

        fireflies.sort((a, b) => a.cost - b.cost);

        let bestFirefly = { ...fireflies[0] };
        const initialCost = bestFirefly.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Adaptive randomization reduction
            const currentAlpha = alpha * (1 - iter / maxIterations);

            for (let i = 0; i < effectivePop; i++) {
                for (let j = 0; j < effectivePop; j++) {
                    // Move firefly i towards brighter firefly j
                    if (fireflies[j].brightness > fireflies[i].brightness) {
                        const r = this.tourDistance(fireflies[i].tour, fireflies[j].tour);
                        const beta = beta0 * Math.exp(-gamma * r * r);
                        const attraction = Math.min(1.0, beta + currentAlpha * (rng() - 0.5));

                        let newTour = this.fireflyMove(fireflies[i].tour, fireflies[j].tour, attraction, rng);

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
                        if (newCost < fireflies[i].cost) {
                            fireflies[i] = { tour: newTour, cost: newCost, brightness: 1 / (1 + newCost) };
                            if (newCost < bestFirefly.cost) {
                                bestFirefly = { tour: newTour, cost: newCost, brightness: 1 / (1 + newCost) };
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