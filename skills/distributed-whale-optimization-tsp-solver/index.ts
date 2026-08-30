/**
 * Whale Optimization Algorithm (WOA) Bubble-Net Hunting Metaheuristic for Traveling Salesperson Problem (TSP).
 * Marine mammal swarm metaheuristic offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N humpback whales.
 * - Encircling prey and search for prey exploration (|A| >= 1).
 * - Bubble-net spiral updating maneuver: D' \cdot e^{b l} \cdot \cos(2\pi l).
 * - 2-Opt local perturbation step.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface WOATSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedWhaleOptimizationTSP {
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
     * Crossover step moving whale towards target (prey or random whale).
     */
    private moveWhale(whaleTour: number[], targetTour: number[], intensity: number, rng: () => number): number[] {
        const n = whaleTour.length;
        const result = [...whaleTour];
        const numSwaps = Math.max(1, Math.round(intensity * n * 0.4));

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
     * Bubble-net logarithmic spiral permutation update.
     */
    private spiralBubbleNet(whaleTour: number[], bestTour: number[], b: number, l: number, rng: () => number): number[] {
        const spiralWeight = Math.min(1.0, Math.abs(Math.exp(b * l) * Math.cos(2 * Math.PI * l)));
        return this.moveWhale(whaleTour, bestTour, spiralWeight, rng);
    }

    /**
     * Solves TSP using Whale Optimization Algorithm.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        b = 1.0, // Spiral shape constant
        rng: () => number = Math.random
    ): WOATSPResult {
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

        // 1. Initialize whale population
        let whales: { tour: number[]; cost: number }[] = [];
        for (let i = 0; i < effectivePop; i++) {
            const tour = this.generateRandomPermutation(n, rng);
            whales.push({ tour, cost: this.computeTourCost(tour) });
        }

        whales.sort((a, b) => a.cost - b.cost);

        let bestWhale = { ...whales[0] };
        const initialCost = bestWhale.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            const a = 2.0 - (iter * (2.0 / maxIterations)); // a linearly decreases from 2 to 0

            for (let i = 0; i < effectivePop; i++) {
                const r = rng();
                const A = 2 * a * r - a;
                const C = 2 * r;
                const p = rng();

                let newTour: number[];

                if (p < 0.5) {
                    if (Math.abs(A) < 1) {
                        // Encircling prey (move towards best whale)
                        newTour = this.moveWhale(whales[i].tour, bestWhale.tour, Math.abs(A) / 2.0, rng);
                    } else {
                        // Search for prey (exploration: move towards random whale)
                        const randWhaleIdx = Math.floor(rng() * effectivePop);
                        newTour = this.moveWhale(whales[i].tour, whales[randWhaleIdx].tour, Math.abs(A) / 2.0, rng);
                    }
                } else {
                    // Bubble-net spiral attack
                    const l = (rng() * 2) - 1; // Uniform in [-1, 1]
                    newTour = this.spiralBubbleNet(whales[i].tour, bestWhale.tour, b, l, rng);
                }

                // 2-opt random walk refinement
                if (rng() < 0.2) {
                    const l = Math.floor(rng() * n);
                    let r = Math.floor(rng() * n);
                    while (r === l) r = Math.floor(rng() * n);
                    const left = Math.min(l, r);
                    const right = Math.max(l, r);
                    let lp = left, rp = right;
                    while (lp < rp) {
                        const tmp = newTour[lp];
                        newTour[lp] = newTour[rp];
                        newTour[rp] = tmp;
                        lp++;
                        rp--;
                    }
                }

                const newCost = this.computeTourCost(newTour);
                if (newCost < whales[i].cost) {
                    whales[i] = { tour: newTour, cost: newCost };
                    if (newCost < bestWhale.cost) {
                        bestWhale = { tour: newTour, cost: newCost };
                    }
                }
            }

            whales.sort((a, b) => a.cost - b.cost);
        }

        const finalTour: string[] = [...bestWhale.tour.map(i => this.points[i].id), this.points[bestWhale.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: bestWhale.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}