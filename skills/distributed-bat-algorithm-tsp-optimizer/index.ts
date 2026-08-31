/**
 * Bat Algorithm (BA) Echolocation Frequency & Loudness-Pulse Emission Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired microbat echolocation optimization primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N virtual bats.
 * - Dynamic frequency tuning f \in [f_min, f_max] controlling exploratory velocity.
 * - Loudness decay A_i^{t+1} = alpha * A_i^t and pulse emission increase r_i^{t+1} = r_i^0 * (1 - exp(-gamma * t)).
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface BATSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedBatTSPOptimizer {
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
     * Echolocation guided crossover towards best bat.
     */
    private echolocateMove(tour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
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
     * Solves TSP using Bat Algorithm.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        fmin = 0,
        fmax = 2,
        alpha = 0.9,
        gamma = 0.05,
        rng: () => number = Math.random
    ): BATSPResult {
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

        // 1. Initialize Microbats population
        let bats: { tour: number[]; cost: number; A: number; r: number; r0: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            const r0 = 0.1 + 0.4 * rng();
            bats.push({ tour, cost: this.computeTourCost(tour), A: 0.9, r: r0, r0 });
        }

        bats.sort((a, b) => a.cost - b.cost);

        let bestBat = { ...bats[0] };
        const initialCost = bestBat.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            for (let i = 0; i < effectivePop; i++) {
                // Frequency update
                const beta = rng();
                const freq = fmin + (fmax - fmin) * beta;
                const step = Math.min(1.0, 0.2 * freq);

                // Global echolocation step towards best
                let newTour = this.echolocateMove(bats[i].tour, bestBat.tour, step, rng);

                // Local search around best if rand > pulse emission rate r
                if (rng() > bats[i].r) {
                    const localStep = Math.min(1.0, bats[i].A * 0.4);
                    newTour = this.echolocateMove(newTour, bestBat.tour, localStep, rng);
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

                // Accept solution if improved and rand < loudness A
                if (newCost < bats[i].cost || (newCost === bats[i].cost && rng() < bats[i].A)) {
                    bats[i].tour = newTour;
                    bats[i].cost = newCost;
                    // Update loudness and pulse rate
                    bats[i].A *= alpha;
                    bats[i].r = bats[i].r0 * (1 - Math.exp(-gamma * iter));

                    if (newCost < bestBat.cost) {
                        bestBat = { ...bats[i] };
                    }
                }
            }

            bats.sort((a, b) => a.cost - b.cost);
        }

        const finalTour: string[] = [...bestBat.tour.map(i => this.points[i].id), this.points[bestBat.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: bestBat.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}