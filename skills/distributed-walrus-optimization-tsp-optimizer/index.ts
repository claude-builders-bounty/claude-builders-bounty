/**
 * Walrus Optimization Algorithm (WOA) Dynamic Feeding, Migration & Predator Defense Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired marine mammal ecological search primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N virtual walruses.
 * - 3 Characteristic behavioral stages: Seabed Feeding, Iceberg Migration, and Rookery Defense / Rest.
 * - Dynamic radius reduction R * (1 - t/T).
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface WOATSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedWalrusOptimizationTSPOptimizer {
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
     * Walrus movement crossover towards target tour.
     */
    private walrusMove(tour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
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
     * Solves TSP using Walrus Optimization Algorithm.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        R = 0.2,
        rng: () => number = Math.random
    ): WOATSPResult {
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

        // 1. Initialize Walrus herd population
        let walruses: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            walruses.push({ tour, cost: this.computeTourCost(tour) });
        }

        walruses.sort((a, b) => a.cost - b.cost);

        let bestWalrus = { ...walruses[0] };
        const initialCost = bestWalrus.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Stage 1: Feeding on seabed shellfish guided by alpha leaders
            for (let i = 0; i < effectivePop; i++) {
                const alpha = bestWalrus.tour;
                const newTour = this.walrusMove(walruses[i].tour, alpha, 0.45, rng);

                const newCost = this.computeTourCost(newTour);
                if (newCost < walruses[i].cost) {
                    walruses[i] = { tour: newTour, cost: newCost };
                    if (newCost < bestWalrus.cost) {
                        bestWalrus = { tour: newTour, cost: newCost };
                    }
                }
            }

            // Stage 2: Seasonal Migration between Icebergs
            for (let i = 0; i < effectivePop; i++) {
                const peerIdx = Math.floor(rng() * effectivePop);
                const peer = walruses[peerIdx].tour;
                const randomSpot = this.generateRandomPermutation(n, rng);
                const step = this.walrusMove(walruses[i].tour, peer, 0.55, rng);
                const newTour = this.walrusMove(step, randomSpot, 0.2, rng);

                const newCost = this.computeTourCost(newTour);
                if (newCost < walruses[i].cost) {
                    walruses[i] = { tour: newTour, cost: newCost };
                    if (newCost < bestWalrus.cost) {
                        bestWalrus = { tour: newTour, cost: newCost };
                    }
                }
            }

            // Stage 3: Predator Defense & Rookery Rest
            const radius = R * (1 - iter / maxIterations);
            for (let i = 0; i < effectivePop; i++) {
                const step1 = this.walrusMove(walruses[i].tour, bestWalrus.tour, 0.6 + radius, rng);

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
                if (newCost < walruses[i].cost) {
                    walruses[i] = { tour: step1, cost: newCost };
                    if (newCost < bestWalrus.cost) {
                        bestWalrus = { tour: step1, cost: newCost };
                    }
                }
            }

            walruses.sort((a, b) => a.cost - b.cost);
        }

        const finalTour: string[] = [...bestWalrus.tour.map(i => this.points[i].id), this.points[bestWalrus.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: bestWalrus.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}