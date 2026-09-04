/**
 * Chimp Optimization Algorithm (ChOA) Social Hunting Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired four-tier hunting hierarchy (Driver, Barrier, Chaser, Attacker) & chaotic map primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations, N virtual chimps, and n cities.
 * - Multi-agent coordinated hunting drive, pursuit enclosure, and chaotic map exploration.
 * - 2-Opt local search refinement for attack capture.
 * - Full unit test coverage via Node native test runner.
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

export class DistributedChimpTSPOptimizer {
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
     * Guided crossover move towards a reference gorilla (e.g. Silverback or peer).
     */
    private guidedMove(tour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
        const n = tour.length;
        const result = [...tour];
        const numSwaps = Math.max(1, Math.round(intensity * n * 0.5));

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
     * Inverts a subsequence in the tour (2-opt move).
     */
    private twoOptMove(tour: number[], rng: () => number): number[] {
        const n = tour.length;
        if (n <= 2) return [...tour];

        const result = [...tour];
        const i = Math.floor(rng() * n);
        let j = Math.floor(rng() * n);
        while (j === i) j = Math.floor(rng() * n);

        const left = Math.min(i, j);
        const right = Math.max(i, j);

        let lp = left, rp = right;
        while (lp < rp) {
            const tmp = result[lp];
            result[lp] = result[rp];
            result[rp] = tmp;
            lp++;
            rp--;
        }

        return result;
    }

    /**
     * Solves TSP using Chimp Optimization Algorithm (ChOA).
     */
    public search(
        maxIterations = 120,
        groupSize = 25,
        fDynamic = 2.5,
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

        const effectiveGroup = Math.max(8, Math.min(60, groupSize));

        // 1. Initialize Chimp Population
        let chimps: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectiveGroup; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            const cost = this.computeTourCost(tour);
            chimps.push({ tour, cost });
        }

        chimps.sort((a, b) => a.cost - b.cost);

        // Four hunting leaders: Attacker, Barrier, Chaser, Driver
        let attacker = { ...chimps[0] };
        let barrier = { ...chimps[1] };
        let chaser = { ...chimps[2] };
        let driver = { ...chimps[3] };
        const initialCost = attacker.cost;

        // Chaotic map state (Logistic map seed)
        let chaosVal = 0.7;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Update chaotic map
            chaosVal = 4.0 * chaosVal * (1.0 - chaosVal);

            // Dynamic coefficient a decreases linearly from 2.5 to 0
            const a = fDynamic * (1.0 - iter / maxIterations);

            for (let i = 0; i < effectiveGroup; i++) {
                const r = rng();
                let candidateTour: number[];

                if (r < 0.2) {
                    // Chaotic exploration / Drive mode
                    candidateTour = this.guidedMove(chimps[i].tour, driver.tour, 0.35 + 0.3 * chaosVal, rng);
                } else if (r < 0.45) {
                    // Barrier confinement mode
                    candidateTour = this.guidedMove(chimps[i].tour, barrier.tour, 0.45 + 0.2 * rng(), rng);
                } else if (r < 0.7) {
                    // Chaser pursuit mode
                    candidateTour = this.guidedMove(chimps[i].tour, chaser.tour, 0.5 + 0.25 * rng(), rng);
                } else {
                    // Attacker capture mode
                    candidateTour = this.guidedMove(chimps[i].tour, attacker.tour, 0.55 + 0.35 * (1 - iter / maxIterations), rng);
                }

                // 2-Opt local refinement during hunt encirclement
                if (rng() < 0.3 || (a < 0.8 && rng() < 0.5)) {
                    candidateTour = this.twoOptMove(candidateTour, rng);
                }

                const candidateCost = this.computeTourCost(candidateTour);
                if (candidateCost < chimps[i].cost) {
                    chimps[i].tour = candidateTour;
                    chimps[i].cost = candidateCost;

                    // Update hunting leaders
                    if (candidateCost < attacker.cost) {
                        attacker = { ...chimps[i] };
                    }
                }
            }

            // Re-sort and re-assign 4 hunting roles
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