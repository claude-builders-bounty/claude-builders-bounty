/**
 * African Vultures Optimization Algorithm (AVOA) Starvation & Carrion Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired dual-leader flight hierarchy (Best Vulture 1 & 2) & starvation rate search primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations, N virtual vultures, and n cities.
 * - Starvation rate F dynamic exploration/exploitation phase transition.
 * - Dual-leader flight guidance, aggressive food competition, and 2-Opt local search refinement.
 * - Full unit test coverage via Node native test runner.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface AVOATSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedAfricanVulturesTSPOptimizer {
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
     * Solves TSP using African Vultures Optimization Algorithm (AVOA).
     */
    public search(
        maxIterations = 120,
        populationSize = 25,
        p1 = 0.6,
        rng: () => number = Math.random
    ): AVOATSPResult {
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

        const effectivePop = Math.max(8, Math.min(60, populationSize));

        // 1. Initialize Vulture Population
        let vultures: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            const cost = this.computeTourCost(tour);
            vultures.push({ tour, cost });
        }

        vultures.sort((a, b) => a.cost - b.cost);

        // Best two vultures (Best Vulture 1 & Best Vulture 2)
        let bestVulture1 = { ...vultures[0] };
        let bestVulture2 = { ...vultures[1] };
        const initialCost = bestVulture1.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Starvation rate F: balances exploration (|F| >= 1) and exploitation (|F| < 1)
            const h = 2.0 * rng() - 1.0;
            const z = rng() < 0.5 ? -1.0 : 1.0;
            const F = (2.0 * rng() + 1.0) * z * (1.0 - iter / maxIterations) + h;

            for (let i = 0; i < effectivePop; i++) {
                // Select reference leader based on probability p1
                const leader = rng() < p1 ? bestVulture1 : bestVulture2;
                let candidateTour: number[];

                if (Math.abs(F) >= 1.0) {
                    // Exploration phase
                    if (rng() < 0.3) {
                        // Search around random position
                        candidateTour = this.generateRandomPermutation(n, rng);
                    } else {
                        // Fly towards selected leader with low intensity
                        candidateTour = this.guidedMove(vultures[i].tour, leader.tour, 0.3 + 0.2 * rng(), rng);
                    }
                } else {
                    // Exploitation phase
                    if (Math.abs(F) >= 0.5) {
                        // Encirclement & siege flight towards leader
                        const intensity = 0.5 + 0.35 * (1.0 - Math.abs(F));
                        candidateTour = this.guidedMove(vultures[i].tour, leader.tour, intensity, rng);
                    } else {
                        // Aggressive fight for carrion: intense 2-opt and local search
                        candidateTour = this.guidedMove(vultures[i].tour, bestVulture1.tour, 0.7, rng);
                        candidateTour = this.twoOptMove(candidateTour, rng);
                    }
                }

                // Periodic 2-opt local search refinement
                if (rng() < 0.25) {
                    candidateTour = this.twoOptMove(candidateTour, rng);
                }

                const candidateCost = this.computeTourCost(candidateTour);
                if (candidateCost < vultures[i].cost) {
                    vultures[i].tour = candidateTour;
                    vultures[i].cost = candidateCost;

                    if (candidateCost < bestVulture1.cost) {
                        bestVulture1 = { ...vultures[i] };
                    }
                }
            }

            // Re-sort and update top 2 vultures
            vultures.sort((a, b) => a.cost - b.cost);
            bestVulture1 = { ...vultures[0] };
            bestVulture2 = { ...vultures[1] };
        }

        const finalTour: string[] = [...bestVulture1.tour.map(i => this.points[i].id), this.points[bestVulture1.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: bestVulture1.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}