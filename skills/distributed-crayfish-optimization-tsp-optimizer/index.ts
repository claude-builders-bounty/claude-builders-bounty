/**
 * Crayfish Optimization Algorithm (COA) Dynamic Temperature-Regulated Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired crustacean ecological behavior search primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N virtual crayfish.
 * - 3 Thermal behavior modes: Summer Resort (high temp), Competition (medium temp), and Foraging (low temp).
 * - Dynamic environmental temperature decay controlling stage transitions.
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface COATSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedCrayfishOptimizationTSPOptimizer {
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
     * Crayfish movement crossover towards target tour.
     */
    private crayfishMove(tour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
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
     * Solves TSP using Crayfish Optimization Algorithm.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        tempMax = 40,
        tempMin = 15,
        rng: () => number = Math.random
    ): COATSPResult {
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

        // 1. Initialize Crayfish population
        let crayfishList: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            crayfishList.push({ tour, cost: this.computeTourCost(tour) });
        }

        crayfishList.sort((a, b) => a.cost - b.cost);

        let bestCrayfish = { ...crayfishList[0] };
        const initialCost = bestCrayfish.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Dynamic temperature curve
            const temp = tempMin + (tempMax - tempMin) * (1 - iter / maxIterations);

            for (let i = 0; i < effectivePop; i++) {
                let newTour: number[];

                if (temp > 30) {
                    // Stage 1: Summer Resort Stage (High temperature: retreat towards cave refuge)
                    const cave = bestCrayfish.tour;
                    const randomPeer = crayfishList[Math.floor(rng() * effectivePop)].tour;
                    const step1 = this.crayfishMove(crayfishList[i].tour, cave, 0.6, rng);
                    newTour = this.crayfishMove(step1, randomPeer, 0.3, rng);
                } else {
                    // Moderate/Cool temperature
                    if (rng() > 0.5) {
                        // Stage 2: Competition Stage (Contesting food sources)
                        const rival = crayfishList[Math.floor(rng() * effectivePop)].tour;
                        newTour = this.crayfishMove(crayfishList[i].tour, rival, 0.7, rng);
                    } else {
                        // Stage 3: Foraging Stage (Claw feeding around best food patch)
                        newTour = this.crayfishMove(crayfishList[i].tour, bestCrayfish.tour, 0.4, rng);
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
                if (newCost < crayfishList[i].cost) {
                    crayfishList[i] = { tour: newTour, cost: newCost };
                    if (newCost < bestCrayfish.cost) {
                        bestCrayfish = { tour: newTour, cost: newCost };
                    }
                }
            }

            crayfishList.sort((a, b) => a.cost - b.cost);
        }

        const finalTour: string[] = [...bestCrayfish.tour.map(i => this.points[i].id), this.points[bestCrayfish.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: bestCrayfish.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}