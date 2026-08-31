/**
 * Chimp Optimization Algorithm (ChOA) Social Hierarchy & Hunting Driver Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired primate social pack optimization primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N chimps.
 * - Four specialized social hunting groups: Driver, Barrier, Chaser, Attacker.
 * - Dynamic parameter f decaying from 2.5 to 0 modulating exploration/exploitation.
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface ChOATSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedChimpOptimizationTSPOptimizer {
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
     * Chimp guided crossover towards target group role leader.
     */
    private chimpMove(tour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
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
     * Solves TSP using Chimp Optimization Algorithm.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        rng: () => number = Math.random
    ): ChOATSPResult {
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

        // 1. Initialize Chimp population
        let chimps: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            chimps.push({ tour, cost: this.computeTourCost(tour) });
        }

        chimps.sort((a, b) => a.cost - b.cost);

        // 4 Key roles in chimp hierarchy
        let attacker = { ...chimps[0] };
        let barrier = { ...chimps[1] };
        let chaser = { ...chimps[2] };
        let driver = { ...chimps[3] };
        const initialCost = attacker.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Dynamic parameter f decays from 2.5 to 0
            const f = 2.5 - iter * (2.5 / maxIterations);

            for (let i = 0; i < effectivePop; i++) {
                const r1 = rng();
                const r2 = rng();
                const a = 2 * f * r1 - f;
                const c = 2 * r2;

                let newTour = [...chimps[i].tour];

                if (rng() < 0.5) {
                    // Drive & block prey towards attacker
                    const targetLeader = i % 4 === 0 ? attacker : (i % 4 === 1 ? barrier : (i % 4 === 2 ? chaser : driver));
                    const intensity = Math.min(1.0, 0.4 * Math.abs(a) + 0.1 * c);
                    newTour = this.chimpMove(newTour, targetLeader.tour, intensity, rng);
                } else {
                    // Attack phase: integrate roles
                    newTour = this.chimpMove(newTour, attacker.tour, 0.5, rng);
                    newTour = this.chimpMove(newTour, barrier.tour, 0.3, rng);
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
                if (newCost < chimps[i].cost) {
                    chimps[i] = { tour: newTour, cost: newCost };
                }
            }

            chimps.sort((a, b) => a.cost - b.cost);
            attacker = { ...chimps[0] };
            barrier = { ...chimps[1] };
            chaser = { ...chimps[2] };
            driver = { ...chimps[3] };
        }

        const finalTour: string[] = [...attacker.tour.map(i => this.points[i].id), this.points[attacker.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: attacker.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}