/**
 * Harris Hawks Optimization (HHO) Cooperative Chasing Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired cooperative raptor surprise pounce search primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N hunting hawks.
 * - Dynamic prey escaping energy E = 2 * E0 * (1 - t / T).
 * - 4 Phase Chasing: Soft besiege, Hard besiege, Soft dive, and Hard dive.
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface HHOTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedHarrisHawksTSPOptimizer {
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
     * Cooperative surprise pounce crossover towards rabbit target.
     */
    private hawkPounce(tour: number[], rabbitTour: number[], intensity: number, rng: () => number): number[] {
        const n = tour.length;
        const result = [...tour];
        const numSwaps = Math.max(1, Math.round(intensity * n * 0.35));

        for (let s = 0; s < numSwaps; s++) {
            const targetIdx = Math.floor(rng() * n);
            const targetVal = rabbitTour[targetIdx];
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
     * Solves TSP using Harris Hawks Optimization.
     */
    public search(
        maxIterations = 100,
        hawkCount = 20,
        rng: () => number = Math.random
    ): HHOTSPResult {
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

        const effectivePop = Math.max(5, Math.min(50, hawkCount));

        // 1. Initialize Harris Hawks population
        let hawks: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            hawks.push({ tour, cost: this.computeTourCost(tour) });
        }

        hawks.sort((a, b) => a.cost - b.cost);

        let rabbit = { ...hawks[0] };
        const initialCost = rabbit.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Escaping energy factor E decays from 2 to 0
            const E0 = 2 * rng() - 1; // [-1, 1]
            const E = 2 * E0 * (1 - iter / maxIterations);
            const absE = Math.abs(E);

            for (let i = 0; i < effectivePop; i++) {
                let newTour: number[];

                if (absE >= 1) {
                    // Exploration phase: perching behavior
                    if (rng() >= 0.5) {
                        const randomHawk = hawks[Math.floor(rng() * effectivePop)];
                        newTour = this.hawkPounce(hawks[i].tour, randomHawk.tour, 0.5, rng);
                    } else {
                        newTour = this.generateRandomPermutation(n, rng);
                    }
                } else {
                    // Exploitation phase: 4 Besiege tactical moves
                    const r = rng();
                    if (r >= 0.5 && absE >= 0.5) {
                        // Soft besiege
                        const J = 2 * (1 - rng()); // Jump strength
                        newTour = this.hawkPounce(hawks[i].tour, rabbit.tour, 0.3 * J, rng);
                    } else if (r >= 0.5 && absE < 0.5) {
                        // Hard besiege
                        newTour = this.hawkPounce(hawks[i].tour, rabbit.tour, 0.7, rng);
                    } else if (r < 0.5 && absE >= 0.5) {
                        // Soft besiege with rapid dive
                        newTour = this.hawkPounce(hawks[i].tour, rabbit.tour, 0.4, rng);
                    } else {
                        // Hard besiege with rapid dive
                        newTour = this.hawkPounce(hawks[i].tour, rabbit.tour, 0.8, rng);
                    }
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
                if (newCost < hawks[i].cost) {
                    hawks[i] = { tour: newTour, cost: newCost };
                    if (newCost < rabbit.cost) {
                        rabbit = { tour: newTour, cost: newCost };
                    }
                }
            }

            hawks.sort((a, b) => a.cost - b.cost);
        }

        const finalTour: string[] = [...rabbit.tour.map(i => this.points[i].id), this.points[rabbit.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: rabbit.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}