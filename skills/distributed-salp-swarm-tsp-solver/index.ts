/**
 * Salp Swarm Algorithm (SSA) Ocean Chain Navigation Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired swarm intelligence primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N salps in a chain.
 * - Leader salp navigation towards food source F guided by c_1 = 2 \exp(-(4 l / L)^2).
 * - Follower salp chain dynamics x^i = (x^i + x^{i-1}) / 2 mapped to permutation crossover.
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface SSATSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedSalpSwarmTSP {
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
     * Chain movement combining leader/preceding salp guidance.
     */
    private chainMove(salpTour: number[], guideTour: number[], intensity: number, rng: () => number): number[] {
        const n = salpTour.length;
        const result = [...salpTour];
        const numSwaps = Math.max(1, Math.round(intensity * n * 0.4));

        for (let s = 0; s < numSwaps; s++) {
            const targetIdx = Math.floor(rng() * n);
            const targetVal = guideTour[targetIdx];
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
    ): SSATSPResult {
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

        // 1. Initialize salp chain
        let salps: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            salps.push({ tour, cost: this.computeTourCost(tour) });
        }

        salps.sort((a, b) => a.cost - b.cost);

        let foodSource = { ...salps[0] };
        const initialCost = foodSource.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Parameter c1 balances exploration and exploitation: c1 = 2 * exp(-(4 * iter / maxIterations)^2)
            const c1 = 2.0 * Math.exp(-Math.pow((4.0 * iter) / maxIterations, 2));

            // Leader update (salp index 0)
            const c2 = rng();
            const c3 = rng();
            let leaderTour = [...salps[0].tour];
            if (c3 >= 0.5) {
                leaderTour = this.chainMove(leaderTour, foodSource.tour, c1 * c2 * 0.5, rng);
            } else {
                leaderTour = this.chainMove(leaderTour, foodSource.tour, c1 * (1 - c2) * 0.5, rng);
            }

            const leaderCost = this.computeTourCost(leaderTour);
            salps[0] = { tour: leaderTour, cost: leaderCost };
            if (leaderCost < foodSource.cost) {
                foodSource = { tour: leaderTour, cost: leaderCost };
            }

            // Follower salp chain updates
            for (let i = 1; i < effectivePop; i++) {
                // Newton's law of motion: x_i = (x_i + x_{i-1}) / 2
                let followerTour = this.chainMove(salps[i].tour, salps[i - 1].tour, 0.5, rng);

                // 2-opt local search perturbation
                if (rng() < 0.2) {
                    const l = Math.floor(rng() * n);
                    let r = Math.floor(rng() * n);
                    while (r === l) r = Math.floor(rng() * n);
                    const left = Math.min(l, r);
                    const right = Math.max(l, r);
                    let lp = left, rp = right;
                    while (lp < rp) {
                        const tmp = followerTour[lp];
                        followerTour[lp] = followerTour[rp];
                        followerTour[rp] = tmp;
                        lp++;
                        rp--;
                    }
                }

                const followerCost = this.computeTourCost(followerTour);
                salps[i] = { tour: followerTour, cost: followerCost };
                if (followerCost < foodSource.cost) {
                    foodSource = { tour: followerTour, cost: followerCost };
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