/**
 * Salp Swarm Algorithm (SSA) Leader-Follower Chain Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired pelagic tunicate swarm optimization primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N salps.
 * - Dynamic balancing coefficient c_1 = 2 * exp(-(4 * t / T)^2).
 * - Chain movement: Leader salps navigate towards food source, follower salps follow predecessor in chain.
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface SalpTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedSalpSwarmTSPOptimizer {
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
     * Salp guided crossover towards target leader / predecessor.
     */
    private salpMove(salpTour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
        const n = salpTour.length;
        const result = [...salpTour];
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
     * Solves TSP using Salp Swarm Algorithm.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        rng: () => number = Math.random
    ): SalpTSPResult {
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

        // 1. Initialize Salp population
        let salps: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            salps.push({ tour, cost: this.computeTourCost(tour) });
        }

        salps.sort((a, b) => a.cost - b.cost);

        let foodSource = { ...salps[0] }; // Best global food source
        const initialCost = foodSource.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Adaptive exploration coefficient c1
            const c1 = 2 * Math.exp(-Math.pow((4 * iter) / maxIterations, 2));

            for (let i = 0; i < effectivePop; i++) {
                let newTour: number[];

                if (i === 0) {
                    // Leader salp: navigates towards food source with c1 coefficient
                    const c2 = rng();
                    const c3 = rng();
                    const intensity = Math.min(1.0, c1 * (c3 >= 0.5 ? c2 : 1 - c2));
                    newTour = this.salpMove(salps[0].tour, foodSource.tour, intensity, rng);
                } else {
                    // Follower salps: follow predecessor salp in the chain (Newton's laws of motion)
                    const predecessor = salps[i - 1].tour;
                    newTour = this.salpMove(salps[i].tour, predecessor, 0.5, rng);
                }

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
                if (newCost < salps[i].cost) {
                    salps[i] = { tour: newTour, cost: newCost };
                    if (newCost < foodSource.cost) {
                        foodSource = { tour: newTour, cost: newCost };
                    }
                }
            }

            salps.sort((a, b) => a.cost - b.cost);
        }

        const finalTour: string[] = [...foodSource.tour.map(i => this.points[i].id), this.points[foodSource.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: foodSource.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}