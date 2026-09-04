/**
 * Artificial Gorilla Troops Optimizer (GTO) Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired troop hierarchy, silverback leadership, and social competition search primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations, N virtual gorillas, and n cities.
 * - Exploration phase: Migration to unknown areas, migration towards troop members, and migration to known locations.
 * - Exploitation phase: Following the silverback leader and competition for adult females with local 2-opt search refinement.
 * - Full unit test coverage via Node native test runner.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface GTOTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedArtificialGorillaTroopsTSPOptimizer {
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
     * Solves TSP using Artificial Gorilla Troops Optimizer (GTO).
     */
    public search(
        maxIterations = 120,
        troopSize = 25,
        p = 0.03,
        beta = 3.0,
        rng: () => number = Math.random
    ): GTOTSPResult {
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

        const effectiveTroop = Math.max(6, Math.min(60, troopSize));

        // 1. Initialize Gorilla Troop
        let troop: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectiveTroop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            const cost = this.computeTourCost(tour);
            troop.push({ tour, cost });
        }

        troop.sort((a, b) => a.cost - b.cost);

        // Best individual is the Silverback
        let silverback = { ...troop[0] };
        const initialCost = silverback.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            const a = (Math.cos(2 * rng()) + 1) * (1 - iter / maxIterations);
            const C = a * (2 * rng() - 1);

            // Phase 1: Exploration Phase
            for (let i = 0; i < effectiveTroop; i++) {
                const randVal = rng();
                let candidateTour: number[];

                if (randVal < p) {
                    candidateTour = this.generateRandomPermutation(n, rng);
                } else if (rng() >= 0.5) {
                    const randomPeerIdx = Math.floor(rng() * effectiveTroop);
                    candidateTour = this.guidedMove(troop[i].tour, troop[randomPeerIdx].tour, 0.4 + 0.3 * rng(), rng);
                } else {
                    candidateTour = this.guidedMove(troop[i].tour, silverback.tour, 0.5 + 0.3 * rng(), rng);
                }

                const candidateCost = this.computeTourCost(candidateTour);
                if (candidateCost < troop[i].cost) {
                    troop[i].tour = candidateTour;
                    troop[i].cost = candidateCost;

                    if (candidateCost < silverback.cost) {
                        silverback = { ...troop[i] };
                    }
                }
            }

            // Phase 2: Exploitation Phase
            const W = 0.8;
            for (let i = 0; i < effectiveTroop; i++) {
                let candidateTour: number[];

                if (Math.abs(C) >= W) {
                    const followIntensity = 0.3 + (1 - iter / maxIterations) * 0.4;
                    candidateTour = this.guidedMove(troop[i].tour, silverback.tour, followIntensity, rng);
                } else {
                    candidateTour = this.twoOptMove(troop[i].tour, rng);
                    if (rng() < 0.3) {
                        candidateTour = this.twoOptMove(candidateTour, rng);
                    }
                }

                if (rng() < 0.25) {
                    candidateTour = this.twoOptMove(candidateTour, rng);
                }

                const candidateCost = this.computeTourCost(candidateTour);
                if (candidateCost < troop[i].cost) {
                    troop[i].tour = candidateTour;
                    troop[i].cost = candidateCost;

                    if (candidateCost < silverback.cost) {
                        silverback = { ...troop[i] };
                    }
                }
            }

            troop.sort((a, b) => a.cost - b.cost);
            if (troop[0].cost < silverback.cost) {
                silverback = { ...troop[0] };
            }
        }

        const finalTour: string[] = [...silverback.tour.map(i => this.points[i].id), this.points[silverback.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: silverback.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}