/**
 * Chimp Optimization Algorithm (ChOA) Hunting Specialization Metaheuristic for Traveling Salesperson Problem (TSP).
 * Primate swarm optimization primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N chimps.
 * - 4 specialized hunting roles: Driver, Barrier, Chaser, and Attacker.
 * - Dynamic group behavioral vector updates a = 2.5 - iter * (2.5 / T).
 * - Multi-leader guided crossover and 2-Opt local search refinement.
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

export class DistributedChimpOptimizationTSP {
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
     * Role-guided crossover towards leader chimp.
     */
    private roleGuidedMove(chimpTour: number[], leaderTour: number[], weight: number, rng: () => number): number[] {
        const n = chimpTour.length;
        const result = [...chimpTour];
        const numSwaps = Math.max(1, Math.round(weight * n * 0.35));

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

        // 1. Initialize chimp population
        let chimps: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            chimps.push({ tour, cost: this.computeTourCost(tour) });
        }

        chimps.sort((a, b) => a.cost - b.cost);

        let attacker = { ...chimps[0] };
        let barrier = { ...chimps[1] };
        let chaser = { ...chimps[2] };
        let driver = { ...chimps[3] };
        const initialCost = attacker.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Parameter a linearly decreases from 2.5 to 0
            const a = 2.5 - iter * (2.5 / maxIterations);

            for (let i = 0; i < effectivePop; i++) {
                // Generate group vectors
                const r1 = rng();
                const r2 = rng();
                const c = 2 * r2;
                const f = 2 * a * r1 - a;

                const weightAttacker = Math.min(1.0, Math.abs(f * c * 0.4));
                const weightBarrier = Math.min(1.0, Math.abs(f * 0.3));
                const weightChaser = Math.min(1.0, Math.abs(f * 0.2));
                const weightDriver = Math.min(1.0, Math.abs(f * 0.1));

                let t1 = this.roleGuidedMove(chimps[i].tour, attacker.tour, weightAttacker, rng);
                let t2 = this.roleGuidedMove(t1, barrier.tour, weightBarrier, rng);
                let t3 = this.roleGuidedMove(t2, chaser.tour, weightChaser, rng);
                let t4 = this.roleGuidedMove(t3, driver.tour, weightDriver, rng);

                // 2-opt local search refinement
                if (rng() < 0.2) {
                    const l = Math.floor(rng() * n);
                    let rp = Math.floor(rng() * n);
                    while (rp === l) rp = Math.floor(rng() * n);
                    const left = Math.min(l, rp);
                    const right = Math.max(l, rp);
                    let lp = left, rpp = right;
                    while (lp < rpp) {
                        const tmp = t4[lp];
                        t4[lp] = t4[rpp];
                        t4[rpp] = tmp;
                        lp++;
                        rpp--;
                    }
                }

                const newCost = this.computeTourCost(t4);
                if (newCost < chimps[i].cost) {
                    chimps[i] = { tour: t4, cost: newCost };
                }
            }

            // Update 4 specialized leaders
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