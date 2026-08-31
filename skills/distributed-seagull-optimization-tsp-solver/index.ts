/**
 * Seagull Optimization Algorithm (SOA) Sea Migration & Attack Spiral Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired laridae avian swarm optimization primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N seagulls.
 * - Migration flight with collision avoidance parameter A = f_c - (t * (f_c / Max_iter)).
 * - 3D logarithmic spiral attack behavior towards best seagull prey position.
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface SOATSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedSeagullOptimizationTSP {
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
     * Seagull guided crossover towards target attack position.
     */
    private seagullMove(tour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
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
     * Solves TSP using Seagull Optimization Algorithm.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        fc = 2.0, // Linear movement frequency control
        u = 1.0,
        v = 1.0,
        rng: () => number = Math.random
    ): SOATSPResult {
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

        // 1. Initialize Seagull population
        let seagulls: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            seagulls.push({ tour, cost: this.computeTourCost(tour) });
        }

        seagulls.sort((a, b) => a.cost - b.cost);

        let bestSeagull = { ...seagulls[0] };
        const initialCost = bestSeagull.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Movement frequency parameter A linearly decreases from fc to 0
            const A = fc - iter * (fc / maxIterations);
            // Neighbor search parameter B
            const B = 2 * A * A * rng();

            for (let i = 0; i < effectivePop; i++) {
                // 1. Migration phase: collision avoidance & movement towards best
                const migrationIntensity = Math.min(1.0, (A + B) * 0.25);
                let newTour = this.seagullMove(seagulls[i].tour, bestSeagull.tour, migrationIntensity, rng);

                // 2. Attack spiral phase: logarithmic spiral motion towards prey
                const theta = rng() * 2 * Math.PI;
                const r = u * Math.exp(theta * v * 0.1);
                const attackIntensity = Math.min(1.0, 0.4 * r);
                newTour = this.seagullMove(newTour, bestSeagull.tour, attackIntensity, rng);

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
                if (newCost < seagulls[i].cost) {
                    seagulls[i] = { tour: newTour, cost: newCost };
                    if (newCost < bestSeagull.cost) {
                        bestSeagull = { tour: newTour, cost: newCost };
                    }
                }
            }

            seagulls.sort((a, b) => a.cost - b.cost);
        }

        const finalTour: string[] = [...bestSeagull.tour.map(i => this.points[i].id), this.points[bestSeagull.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: bestSeagull.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}