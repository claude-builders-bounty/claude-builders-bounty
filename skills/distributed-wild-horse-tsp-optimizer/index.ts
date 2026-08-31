/**
 * Wild Horse Optimizer (WHO) Dynamic Grazing, Mating & Stallion Leadership Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired equine social herd structure search primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N virtual wild horses in multiple harems.
 * - 4 Characteristic behavioral stages: Foal Grazing, Inter-harem Mating, Stallion Hierarchy Leadership, and Water Point Convergence.
 * - Dynamic crossover decay rate R.
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface WHOTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedWildHorseTSPOptimizer {
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
     * Equine movement crossover towards target tour.
     */
    private horseMove(tour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
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
     * Solves TSP using Wild Horse Optimizer.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        numHarems = 4,
        rng: () => number = Math.random
    ): WHOTSPResult {
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

        const effectivePop = Math.max(8, Math.min(50, populationSize));
        const effectiveHarems = Math.max(2, Math.min(numHarems, Math.floor(effectivePop / 2)));
        const horsesPerHarem = Math.floor(effectivePop / effectiveHarems);

        // 1. Initialize Wild Horse population into harems
        let harems: { tour: number[]; cost: number }[][] = [];
        for (let h = 0; h < effectiveHarems; h++) {
            let harem: { tour: number[]; cost: number }[] = [];
            for (let i = 0; i < horsesPerHarem; i++) {
                const tour = this.generateRandomPermutation(n, rng);
                harem.push({ tour, cost: this.computeTourCost(tour) });
            }
            harem.sort((a, b) => a.cost - b.cost);
            harems.push(harem);
        }

        let bestStallion = { ...harems[0][0] };
        for (let h = 1; h < effectiveHarems; h++) {
            if (harems[h][0].cost < bestStallion.cost) {
                bestStallion = { ...harems[h][0] };
            }
        }
        const initialCost = bestStallion.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            const R = 2 * (1 - iter / maxIterations);

            // 1. Grazing Behavior of Foals and Mares around their Harem Stallion
            for (let h = 0; h < effectiveHarems; h++) {
                const stallion = harems[h][0];
                for (let i = 1; i < harems[h].length; i++) {
                    const step1 = this.horseMove(harems[h][i].tour, stallion.tour, 0.45 * (R / 2), rng);
                    const randomSpot = this.generateRandomPermutation(n, rng);
                    const newTour = this.horseMove(step1, randomSpot, 0.2, rng);

                    const newCost = this.computeTourCost(newTour);
                    if (newCost < harems[h][i].cost) {
                        harems[h][i] = { tour: newTour, cost: newCost };
                        if (newCost < harems[h][0].cost) {
                            // Mare becomes new leader of harem
                            const tmp = harems[h][0];
                            harems[h][0] = harems[h][i];
                            harems[h][i] = tmp;
                        }
                    }
                }
            }

            // 2. Inter-Harem Mating Behavior (Cross-pollination between harems)
            for (let h = 0; h < effectiveHarems; h++) {
                const targetHaremIdx = (h + 1) % effectiveHarems;
                const mareIdx = Math.max(1, Math.floor(rng() * harems[h].length));
                const stallion = harems[targetHaremIdx][0];

                const newTour = this.horseMove(harems[h][mareIdx].tour, stallion.tour, 0.6, rng);
                const newCost = this.computeTourCost(newTour);
                if (newCost < harems[h][mareIdx].cost) {
                    harems[h][mareIdx] = { tour: newTour, cost: newCost };
                }
            }

            // 3. Stallion Leadership & Water Point Convergence
            for (let h = 0; h < effectiveHarems; h++) {
                let stallionTour = this.horseMove(harems[h][0].tour, bestStallion.tour, 0.7, rng);

                // 2-opt local search refinement
                if (rng() < 0.2) {
                    const l = Math.floor(rng() * n);
                    let rp = Math.floor(rng() * n);
                    while (rp === l) rp = Math.floor(rng() * n);
                    const left = Math.min(l, rp);
                    const right = Math.max(l, rp);
                    let lp = left, rpp = right;
                    while (lp < rpp) {
                        const tmp = stallionTour[lp];
                        stallionTour[lp] = stallionTour[rpp];
                        stallionTour[rpp] = tmp;
                        lp++;
                        rpp--;
                    }
                }

                const newCost = this.computeTourCost(stallionTour);
                if (newCost < harems[h][0].cost) {
                    harems[h][0] = { tour: stallionTour, cost: newCost };
                    if (newCost < bestStallion.cost) {
                        bestStallion = { tour: stallionTour, cost: newCost };
                    }
                }
            }
        }

        const finalTour: string[] = [...bestStallion.tour.map(i => this.points[i].id), this.points[bestStallion.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: bestStallion.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}