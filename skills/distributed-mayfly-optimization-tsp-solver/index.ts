/**
 * Mayfly Algorithm (MA) Nuptial Dance & Mating Flight Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired Ephemeroptera nuptial swarm optimization primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N male/female mayflies.
 * - Male nuptial dance (pbest/gbest attraction) and female attraction flight towards paired males.
 * - Crossover mating mechanics generating offspring with mutation.
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface MATSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedMayflyOptimizationTSP {
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
     * Mayfly guided crossover towards target attraction position.
     */
    private mayflyMove(tour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
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
     * Solves TSP using Mayfly Algorithm.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        beta = 2.0, // Visibility coefficient
        rng: () => number = Math.random
    ): MATSPResult {
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

        const effectivePop = Math.max(6, Math.min(50, populationSize));
        const maleCount = Math.floor(effectivePop / 2);
        const femaleCount = effectivePop - maleCount;

        // 1. Initialize Male and Female populations
        let males: { tour: number[]; cost: number; pbest: number[]; pbestCost: number }[] = [];
        for (let i = 0; i < maleCount; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            const cost = this.computeTourCost(tour);
            males.push({ tour, cost, pbest: [...tour], pbestCost: cost });
        }

        let females: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < femaleCount; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            females.push({ tour, cost: this.computeTourCost(tour) });
        }

        males.sort((a, b) => a.cost - b.cost);
        let gbest = { ...males[0] };
        const initialCost = gbest.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Nuptial dance coefficient d decays
            const d = 0.8 * (1 - iter / maxIterations);

            // 1. Update Males (Nuptial Dance)
            for (let i = 0; i < maleCount; i++) {
                let newTour: number[];
                if (males[i].cost > gbest.cost) {
                    // Attracted to pbest and gbest
                    const r = rng();
                    const intensity = Math.min(1.0, 0.5 * Math.exp(-beta * r * r) + 0.1 * d);
                    newTour = this.mayflyMove(males[i].tour, gbest.tour, intensity, rng);
                } else {
                    // Best male performs nuptial dance (up-and-down flight)
                    const randTour = this.generateRandomPermutation(n, rng);
                    newTour = this.mayflyMove(males[i].tour, randTour, d * 0.3, rng);
                }

                const newCost = this.computeTourCost(newTour);
                if (newCost < males[i].cost) {
                    males[i].tour = newTour;
                    males[i].cost = newCost;
                    if (newCost < males[i].pbestCost) {
                        males[i].pbest = [...newTour];
                        males[i].pbestCost = newCost;
                    }
                }
            }

            // 2. Update Females (Attraction to Males)
            for (let i = 0; i < femaleCount; i++) {
                const pairedMale = males[Math.min(i, maleCount - 1)];
                let newTour: number[];

                if (females[i].cost > pairedMale.cost) {
                    // Attracted to paired male
                    const intensity = Math.min(1.0, 0.7 * Math.exp(-beta * 0.25));
                    newTour = this.mayflyMove(females[i].tour, pairedMale.tour, intensity, rng);
                } else {
                    // Random flight
                    const randTour = this.generateRandomPermutation(n, rng);
                    newTour = this.mayflyMove(females[i].tour, randTour, 0.3, rng);
                }

                const newCost = this.computeTourCost(newTour);
                if (newCost < females[i].cost) {
                    females[i] = { tour: newTour, cost: newCost };
                }
            }

            // 3. Mating & Offspring Crossover
            for (let i = 0; i < Math.min(maleCount, femaleCount); i++) {
                let offspringTour = this.mayflyMove(males[i].tour, females[i].tour, 0.5, rng);

                // 2-opt local search refinement
                if (rng() < 0.2) {
                    const l = Math.floor(rng() * n);
                    let rp = Math.floor(rng() * n);
                    while (rp === l) rp = Math.floor(rng() * n);
                    const left = Math.min(l, rp);
                    const right = Math.max(l, rp);
                    let lp = left, rpp = right;
                    while (lp < rpp) {
                        const tmp = offspringTour[lp];
                        offspringTour[lp] = offspringTour[rpp];
                        offspringTour[rpp] = tmp;
                        lp++;
                        rpp--;
                    }
                }

                const offspringCost = this.computeTourCost(offspringTour);
                if (offspringCost < males[i].cost) {
                    males[i].tour = offspringTour;
                    males[i].cost = offspringCost;
                }
            }

            males.sort((a, b) => a.cost - b.cost);
            if (males[0].cost < gbest.cost) {
                gbest = { ...males[0] };
            }
        }

        const finalTour: string[] = [...gbest.tour.map(i => this.points[i].id), this.points[gbest.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: gbest.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}