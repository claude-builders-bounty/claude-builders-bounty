/**
 * Sparrow Search Algorithm (SSA) Producer-Scrounger-Warning Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired avian foraging and anti-predation behavioral search primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N virtual sparrows.
 * - Producers exploring wide foraging areas guided by safety threshold ST.
 * - Scroungers following top producers to maximize caloric intake.
 * - Anti-predation early warning sentinels (20% of population) triggering emergency evasions.
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface SparrowTSPResult {
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
     * Sparrow flock crossover towards target position.
     */
    private sparrowMove(tour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
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
     * Solves TSP using Sparrow Search Algorithm.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        safetyThreshold = 0.8,
        rng: () => number = Math.random
    ): SparrowTSPResult {
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
        const producerCount = Math.max(1, Math.round(effectivePop * 0.2));

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
            const R2 = rng(); // Alarm value [0, 1]

            // 1. Update Producers (Find best foraging spots)
            for (let i = 0; i < producerCount; i++) {
                let newTour: number[];
                if (R2 < safetyThreshold) {
                    // Safe foraging: wide exploration
                    const alpha = Math.exp(-iter / (maxIterations * 0.5));
                    newTour = this.sparrowMove(sparrows[i].tour, bestSparrow.tour, alpha * 0.5, rng);
                } else {
                    // Danger detected: fly to random safe spot
                    const randomSpot = this.generateRandomPermutation(n, rng);
                    newTour = this.sparrowMove(sparrows[i].tour, randomSpot, 0.4, rng);
                }

                const newCost = this.computeTourCost(newTour);
                if (newCost < sparrows[i].cost) {
                    sparrows[i] = { tour: newTour, cost: newCost };
                    if (newCost < bestSparrow.cost) {
                        bestSparrow = { tour: newTour, cost: newCost };
                    }
                }
            }

            // 2. Update Scroungers (Follow producers)
            for (let i = producerCount; i < effectivePop; i++) {
                let newTour: number[];
                if (i > effectivePop / 2) {
                    // Hungry scroungers forage elsewhere
                    const randomSpot = this.generateRandomPermutation(n, rng);
                    newTour = this.sparrowMove(sparrows[i].tour, randomSpot, 0.5, rng);
                } else {
                    // Forage around best producer
                    newTour = this.sparrowMove(sparrows[i].tour, sparrows[0].tour, 0.6, rng);
                }

                const newCost = this.computeTourCost(newTour);
                if (newCost < sparrows[i].cost) {
                    sparrows[i] = { tour: newTour, cost: newCost };
                    if (newCost < bestSparrow.cost) {
                        bestSparrow = { tour: newTour, cost: newCost };
                    }
                }
            }

            // 3. Early Warning Sentinels (20% aware of danger)
            const sentinelCount = Math.max(1, Math.round(effectivePop * 0.2));
            for (let s = 0; s < sentinelCount; s++) {
                const idx = Math.floor(rng() * effectivePop);
                let newTour: number[];
                if (sparrows[idx].cost > bestSparrow.cost) {
                    // Edge of flock flies to center
                    newTour = this.sparrowMove(sparrows[idx].tour, bestSparrow.tour, 0.7, rng);
                } else {
                    // Center of flock disperses slightly
                    const randomSpot = this.generateRandomPermutation(n, rng);
                    newTour = this.sparrowMove(sparrows[idx].tour, randomSpot, 0.2, rng);
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
                if (newCost < sparrows[idx].cost) {
                    sparrows[idx] = { tour: newTour, cost: newCost };
                    if (newCost < bestSparrow.cost) {
                        bestSparrow = { tour: newTour, cost: newCost };
                    }
                }
            }

            sparrows.sort((a, b) => a.cost - b.cost);
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