/**
 * Jaya Algorithm (JA) Parameterless Victory-Oriented Metaheuristic for Traveling Salesperson Problem (TSP).
 * Simple, algorithm-specific-parameter-free global search primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N candidate solutions.
 * - Simultaneous attraction towards global best solution and repulsion from worst solution.
 * - Greedy selection accepting only strictly better permutations.
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface JayaTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedJayaTSPOptimizer {
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
     * Jaya crossover: attracts towards best tour and repulses away from worst tour.
     */
    private jayaMove(tour: number[], bestTour: number[], worstTour: number[], rng: () => number): number[] {
        const n = tour.length;
        const result = [...tour];

        // 1. Attraction towards best solution
        const r1 = rng();
        const numBestSwaps = Math.max(1, Math.round(r1 * n * 0.3));
        for (let s = 0; s < numBestSwaps; s++) {
            const targetIdx = Math.floor(rng() * n);
            const targetVal = bestTour[targetIdx];
            const currIdx = result.indexOf(targetVal);
            if (currIdx !== -1 && currIdx !== targetIdx) {
                const tmp = result[targetIdx];
                result[targetIdx] = result[currIdx];
                result[currIdx] = tmp;
            }
        }

        // 2. Repulsion away from worst solution
        const r2 = rng();
        if (r2 < 0.5) {
            const worstIdx = Math.floor(rng() * n);
            const worstVal = worstTour[worstIdx];
            const currIdx = result.indexOf(worstVal);
            if (currIdx === worstIdx) {
                // Perturb away from worst position
                const swapWith = (currIdx + 1 + Math.floor(rng() * (n - 1))) % n;
                const tmp = result[currIdx];
                result[currIdx] = result[swapWith];
                result[swapWith] = tmp;
            }
        }

        return result;
    }

    /**
     * Solves TSP using Jaya Algorithm.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        rng: () => number = Math.random
    ): JayaTSPResult {
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
            const bestTour = population[0].tour;
            const worstTour = population[population.length - 1].tour;

            for (let i = 0; i < effectivePop; i++) {
                let newTour = this.jayaMove(population[i].tour, bestTour, worstTour, rng);

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

                // Greedy selection: update if new solution is strictly better
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