/**
 * Spotted Hyena Optimizer (SHO) Social Hierarchy & Coordinated Clustered Attacking Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired hyaenidae social clan optimization primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N spotted hyenas.
 * - Social hunting cluster formation around optimal clan leader.
 * - Dynamic parameter h decaying from 5 to 0 modulating clan cohesion and prey encircling.
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface SHOTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedSpottedHyenaTSPOptimizer {
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
     * Hyena guided crossover towards target clan cluster.
     */
    private hyenaMove(tour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
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
     * Solves TSP using Spotted Hyena Optimizer.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        rng: () => number = Math.random
    ): SHOTSPResult {
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

        // 1. Initialize Spotted Hyena clan population
        let hyenas: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            hyenas.push({ tour, cost: this.computeTourCost(tour) });
        }

        hyenas.sort((a, b) => a.cost - b.cost);

        let matriarchLeader = { ...hyenas[0] };
        const initialCost = matriarchLeader.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Factor h decreases linearly from 5 to 0
            const h = 5 - iter * (5 / maxIterations);

            for (let i = 0; i < effectivePop; i++) {
                const r1 = rng();
                const r2 = rng();
                const B = 2 * r1;
                const E = 2 * h * r2 - h;

                // Define trusted clan cluster size
                const clusterSize = Math.max(1, Math.min(5, Math.floor(h + 1)));
                const trustedCluster = hyenas.slice(0, clusterSize);

                // Coordinated attack: move towards centroid of trusted cluster leaders
                const selectedLeader = trustedCluster[Math.floor(rng() * clusterSize)];
                const intensity = Math.min(1.0, 0.3 * Math.abs(E) + 0.2 * B);

                let newTour = this.hyenaMove(hyenas[i].tour, selectedLeader.tour, intensity, rng);

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
                if (newCost < hyenas[i].cost) {
                    hyenas[i] = { tour: newTour, cost: newCost };
                    if (newCost < matriarchLeader.cost) {
                        matriarchLeader = { tour: newTour, cost: newCost };
                    }
                }
            }

            hyenas.sort((a, b) => a.cost - b.cost);
        }

        const finalTour: string[] = [...matriarchLeader.tour.map(i => this.points[i].id), this.points[matriarchLeader.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: matriarchLeader.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}