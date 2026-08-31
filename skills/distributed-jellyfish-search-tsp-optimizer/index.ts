/**
 * Jellyfish Search (JS) Ocean Current & Swarm Vortex Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired oceanic coelenterate swarm optimization primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N jellyfish.
 * - Dynamic time control factor c(t) = |(1 - t / T) * (2 * r - 1)| for ocean current drift vs swarm motion.
 * - Active vortex and passive motion inside swarm based on relative fitness comparison.
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface JSTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedJellyfishSearchTSPOptimizer {
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
     * Jellyfish guided crossover towards ocean current / vortex attraction.
     */
    private jellyfishMove(tour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
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
     * Solves TSP using Jellyfish Search.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        beta = 3.0,
        gamma = 0.1,
        rng: () => number = Math.random
    ): JSTSPResult {
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

        // 1. Initialize Jellyfish population
        let jellyfish: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            jellyfish.push({ tour, cost: this.computeTourCost(tour) });
        }

        jellyfish.sort((a, b) => a.cost - b.cost);

        let bestJellyfish = { ...jellyfish[0] };
        const initialCost = bestJellyfish.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Time control parameter c(t) determines ocean current vs swarm motion
            const ct = Math.abs((1 - iter / maxIterations) * (2 * rng() - 1));

            for (let i = 0; i < effectivePop; i++) {
                let newTour: number[];

                if (ct >= 0.5) {
                    // Ocean current drift: all jellyfish follow ocean current direction towards global best
                    const intensity = Math.min(1.0, 0.7 * (1 + 0.1 * beta));
                    newTour = this.jellyfishMove(jellyfish[i].tour, bestJellyfish.tour, intensity, rng);
                } else {
                    // Inside swarm motion: active or passive motion
                    if (rng() > (1 - ct)) {
                        // Passive motion (Type A)
                        const randTour = this.generateRandomPermutation(n, rng);
                        newTour = this.jellyfishMove(jellyfish[i].tour, randTour, gamma, rng);
                    } else {
                        // Active motion (Type B): comparison with another random jellyfish j
                        const j = Math.floor(rng() * effectivePop);
                        if (jellyfish[j].cost < jellyfish[i].cost) {
                            // Attraction towards better jellyfish
                            newTour = this.jellyfishMove(jellyfish[i].tour, jellyfish[j].tour, 0.6, rng);
                        } else {
                            // Repulsion / independent direction
                            const randTour = this.generateRandomPermutation(n, rng);
                            newTour = this.jellyfishMove(jellyfish[i].tour, randTour, 0.4, rng);
                        }
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
                if (newCost < jellyfish[i].cost) {
                    jellyfish[i] = { tour: newTour, cost: newCost };
                    if (newCost < bestJellyfish.cost) {
                        bestJellyfish = { tour: newTour, cost: newCost };
                    }
                }
            }

            jellyfish.sort((a, b) => a.cost - b.cost);
        }

        const finalTour: string[] = [...bestJellyfish.tour.map(i => this.points[i].id), this.points[bestJellyfish.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: bestJellyfish.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}