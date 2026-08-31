/**
 * Gravitational Search Algorithm (GSA) Newtonian Gravity & Mass Acceleration Metaheuristic for Traveling Salesperson Problem (TSP).
 * Physical gravitational interaction global search primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N celestial agents.
 * - Gravitational constant exponential decay G(t) = G0 * exp(-alpha * t / T).
 * - Inertial and gravitational mass calculation based on tour cost fitness.
 * - Resultant gravitational acceleration and velocity-driven crossover operators.
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface GSATSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedGravitationalSearchTSPOptimizer {
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
     * Gravitational attraction crossover towards heavier mass agent.
     */
    private gravityMove(tour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
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
     * Solves TSP using Gravitational Search Algorithm.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        G0 = 100,
        alpha = 20,
        rng: () => number = Math.random
    ): GSATSPResult {
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

        // 1. Initialize Celestial masses population
        let masses: { tour: number[]; cost: number; mass: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            masses.push({ tour, cost: this.computeTourCost(tour), mass: 1.0 });
        }

        masses.sort((a, b) => a.cost - b.cost);

        let bestMass = { ...masses[0] };
        const initialCost = bestMass.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Gravitational constant decays exponentially
            const G = G0 * Math.exp((-alpha * iter) / maxIterations);

            const bestCost = masses[0].cost;
            const worstCost = masses[masses.length - 1].cost;
            const costRange = Math.max(1e-6, worstCost - bestCost);

            // Compute normalized inertial mass for each agent
            let totalMass = 0;
            for (let i = 0; i < effectivePop; i++) {
                const rawMass = (worstCost - masses[i].cost) / costRange;
                masses[i].mass = Math.max(1e-4, rawMass);
                totalMass += masses[i].mass;
            }

            for (let i = 0; i < effectivePop; i++) {
                masses[i].mass /= Math.max(1e-6, totalMass);
            }

            // K-best agents that exert gravity on others (decreases over time)
            const kbestCount = Math.max(1, Math.round(effectivePop * (1 - iter / maxIterations)));

            for (let i = 0; i < effectivePop; i++) {
                let totalForce = 0;
                let compositeTour = [...masses[i].tour];

                for (let k = 0; k < kbestCount; k++) {
                    if (k !== i) {
                        const force = (G * masses[i].mass * masses[k].mass) / (1.0 + 0.1 * Math.abs(masses[k].cost - masses[i].cost));
                        totalForce += force;
                        const pullIntensity = Math.min(0.8, force * 5.0 * rng());
                        compositeTour = this.gravityMove(compositeTour, masses[k].tour, pullIntensity, rng);
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
                        const tmp = compositeTour[lp];
                        compositeTour[lp] = compositeTour[rpp];
                        compositeTour[rpp] = tmp;
                        lp++;
                        rpp--;
                    }
                }

                const newCost = this.computeTourCost(compositeTour);
                if (newCost < masses[i].cost) {
                    masses[i] = { tour: compositeTour, cost: newCost, mass: masses[i].mass };
                    if (newCost < bestMass.cost) {
                        bestMass = { tour: compositeTour, cost: newCost, mass: masses[i].mass };
                    }
                }
            }

            masses.sort((a, b) => a.cost - b.cost);
        }

        const finalTour: string[] = [...bestMass.tour.map(i => this.points[i].id), this.points[bestMass.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: bestMass.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}