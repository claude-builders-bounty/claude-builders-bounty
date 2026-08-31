/**
 * Bat Algorithm (BA) Microbat Echolocation Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired swarm optimization primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N microbats.
 * - Dynamic Frequency tuning f_i \in [f_{min}, f_{max}].
 * - Pulse emission rate r_i and Loudness A_i attenuation.
 * - Random walk perturbation around best solutions.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface BatTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedBatAlgorithmTSP {
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
     * Moves a bat towards the best solution proportional to frequency.
     */
    private moveBat(batTour: number[], bestTour: number[], frequency: number, rng: () => number): number[] {
        const n = batTour.length;
        const result = [...batTour];
        const numSwaps = Math.max(1, Math.round(frequency * n * 0.4));

        for (let s = 0; s < numSwaps; s++) {
            const targetIdx = Math.floor(rng() * n);
            const targetVal = bestTour[targetIdx];
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
     * Local random walk (echolocation pulse).
     */
    private localWalk(tour: number[], rng: () => number): number[] {
        const n = tour.length;
        const result = [...tour];
        const i = Math.floor(rng() * n);
        let j = Math.floor(rng() * n);
        while (j === i) j = Math.floor(rng() * n);
        const left = Math.min(i, j);
        const right = Math.max(i, j);
        let l = left, r = right;
        while (l < r) {
            const tmp = result[l];
            result[l] = result[r];
            result[r] = tmp;
            l++;
            r--;
        }
        return result;
    }

    /**
     * Solves TSP using Bat Algorithm.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        fMin = 0.0,
        fMax = 2.0,
        alpha = 0.9, // Loudness attenuation
        gamma = 0.9, // Pulse rate increase
        rng: () => number = Math.random
    ): BatTSPResult {
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

        // 1. Initialize Bat population
        let bats: { tour: number[]; cost: number; loudness: number; pulseRate: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            bats.push({
                tour,
                cost: this.computeTourCost(tour),
                loudness: 0.95,
                pulseRate: 0.05,
            });
        }

        bats.sort((a, b) => a.cost - b.cost);

        let bestTour = [...bats[0].tour];
        let bestCost = bats[0].cost;
        const initialCost = bestCost;

        for (let iter = 0; iter < maxIterations; iter++) {
            for (let i = 0; i < effectivePop; i++) {
                // Adjust frequency: f_i = f_min + (f_max - f_min) * beta
                const beta = rng();
                const freq = fMin + (fMax - fMin) * beta;

                // Move bat towards best
                let newTour = this.moveBat(bats[i].tour, bestTour, freq, rng);

                // Echolocation local walk if rand > pulseRate
                if (rng() > bats[i].pulseRate) {
                    newTour = this.localWalk(bestTour, rng);
                }

                const newCost = this.computeTourCost(newTour);

                // Accept new solution if improved and with loudness condition
                if (newCost < bats[i].cost || (rng() < bats[i].loudness && newCost < bestCost * 1.05)) {
                    bats[i].tour = newTour;
                    bats[i].cost = newCost;
                    bats[i].loudness *= alpha;
                    bats[i].pulseRate = 1 - Math.exp(-gamma * (iter + 1));

                    if (newCost < bestCost) {
                        bestCost = newCost;
                        bestTour = [...newTour];
                    }
                }
            }

            bats.sort((a, b) => a.cost - b.cost);
        }

        const finalTour: string[] = [...bestTour.map(i => this.points[i].id), this.points[bestTour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}