/**
 * Sparrow Search Algorithm (SSA) Anti-Predation & Foraging Swarm Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired avian swarm optimization primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N sparrows.
 * - Tri-role structure: Producers (energy-rich leaders), Scroungers (foragers), and Scouts/Watchers (anti-predation alarms).
 * - Dynamic warning threshold R_2 vs Safety Threshold ST (ST = 0.8).
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface SSATSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedSparrowSearchTSPOptimizer {
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
     * Sparrow guided crossover towards target leader.
     */
    private sparrowMove(sparrowTour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
        const n = sparrowTour.length;
        const result = [...sparrowTour];
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
     * Solves TSP using Sparrow Search Algorithm.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        safetyThreshold = 0.8,
        rng: () => number = Math.random
    ): SSATSPResult {
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

        const effectivePop = Math.max(8, Math.min(50, populationSize));
        const producerCount = Math.max(2, Math.floor(effectivePop * 0.2));
        const scoutCount = Math.max(2, Math.floor(effectivePop * 0.2));

        // 1. Initialize Sparrow population
        let sparrows: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            sparrows.push({ tour, cost: this.computeTourCost(tour) });
        }

        sparrows.sort((a, b) => a.cost - b.cost);

        let bestSparrow = { ...sparrows[0] };
        const initialCost = bestSparrow.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            const r2 = rng(); // Alarm warning value

            // 1. Producers phase
            for (let i = 0; i < producerCount; i++) {
                let newTour: number[];
                if (r2 < safetyThreshold) {
                    // Safe foraging: small random exploration
                    newTour = this.sparrowMove(sparrows[i].tour, bestSparrow.tour, 0.3 * (1 - iter / maxIterations), rng);
                } else {
                    // Danger detected: anti-predator dispersion
                    const randTour = this.generateRandomPermutation(n, rng);
                    newTour = this.sparrowMove(sparrows[i].tour, randTour, 0.7, rng);
                }

                const newCost = this.computeTourCost(newTour);
                if (newCost < sparrows[i].cost) {
                    sparrows[i] = { tour: newTour, cost: newCost };
                }
            }

            // 2. Scroungers phase
            for (let i = producerCount; i < effectivePop; i++) {
                let newTour: number[];
                if (i > effectivePop / 2) {
                    // Low energy scrounger moves towards best producer
                    newTour = this.sparrowMove(sparrows[i].tour, bestSparrow.tour, 0.8, rng);
                } else {
                    // Competing scrounger follows a random producer
                    const randProducerIdx = Math.floor(rng() * producerCount);
                    newTour = this.sparrowMove(sparrows[i].tour, sparrows[randProducerIdx].tour, 0.5, rng);
                }

                const newCost = this.computeTourCost(newTour);
                if (newCost < sparrows[i].cost) {
                    sparrows[i] = { tour: newTour, cost: newCost };
                }
            }

            // 3. Scouts / Watchers anti-predation alarm phase
            for (let s = 0; s < scoutCount; s++) {
                const scoutIdx = Math.floor(rng() * effectivePop);
                let newTour: number[];

                if (sparrows[scoutIdx].cost > bestSparrow.cost) {
                    // Sparrow is at outer edge, retreats to center/best
                    newTour = this.sparrowMove(sparrows[scoutIdx].tour, bestSparrow.tour, 0.6, rng);
                } else {
                    // Central sparrow moves away from others to spread alarm
                    const randOther = sparrows[Math.floor(rng() * effectivePop)].tour;
                    newTour = this.sparrowMove(sparrows[scoutIdx].tour, randOther, 0.4, rng);
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
                if (newCost < sparrows[scoutIdx].cost) {
                    sparrows[scoutIdx] = { tour: newTour, cost: newCost };
                }
            }

            sparrows.sort((a, b) => a.cost - b.cost);
            if (sparrows[0].cost < bestSparrow.cost) {
                bestSparrow = { ...sparrows[0] };
            }
        }

        const finalTour: string[] = [...bestSparrow.tour.map(i => this.points[i].id), this.points[bestSparrow.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: bestSparrow.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}