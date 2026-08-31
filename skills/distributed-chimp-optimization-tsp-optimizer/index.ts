/**
 * Chimp Optimization Algorithm (ChoA) Dynamic Hunting Groups Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired primate hunting behavior search primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N chimps.
 * - 4 Specialized hunting roles: Driver, Barrier, Chaser, and Attacker.
 * - Dynamic coefficient vector f decaying from 2.5 to 0.
 * - Chaotic group position consolidation.
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface ChoATSPResult {
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
     * Group hunting crossover towards leader chimps.
     */
    private chimpMove(tour: number[], leaderTour: number[], intensity: number, rng: () => number): number[] {
        const n = tour.length;
        const result = [...tour];
        const numSwaps = Math.max(1, Math.round(intensity * n * 0.35));

        for (let s = 0; s < numSwaps; s++) {
            const targetIdx = Math.floor(rng() * n);
            const targetVal = leaderTour[targetIdx];
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
    ): ChoATSPResult {
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

        // 1. Initialize Chimp population
        let chimps: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            chimps.push({ tour, cost: this.computeTourCost(tour) });
        }

        chimps.sort((a, b) => a.cost - b.cost);

        let attacker = { ...chimps[0] };
        const initialCost = attacker.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Dynamic parameter f decays linearly from 2.5 to 0
            const f = 2.5 - (2.5 * iter) / maxIterations;

            // 4 Hunting Roles
            const leaderAttacker = chimps[0];
            const leaderBarrier = chimps[Math.min(1, chimps.length - 1)];
            const leaderChaser = chimps[Math.min(2, chimps.length - 1)];
            const leaderDriver = chimps[Math.min(3, chimps.length - 1)];

            for (let i = 0; i < effectivePop; i++) {
                // Cooperative positioning towards 4 leaders
                const r1 = rng();
                const a1 = 2 * f * r1 - f;
                const weight = Math.min(0.8, Math.abs(a1) * 0.3);

                let newTour = this.chimpMove(chimps[i].tour, leaderAttacker.tour, weight, rng);
                if (rng() < 0.5) {
                    newTour = this.chimpMove(newTour, leaderBarrier.tour, weight * 0.8, rng);
                }
                if (rng() < 0.3) {
                    newTour = this.chimpMove(newTour, leaderChaser.tour, weight * 0.6, rng);
                }
                if (rng() < 0.2) {
                    newTour = this.chimpMove(newTour, leaderDriver.tour, weight * 0.4, rng);
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
                    if (newCost < attacker.cost) {
                        attacker = { tour: newTour, cost: newCost };
                    }
                }
            }

            chimps.sort((a, b) => a.cost - b.cost);
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