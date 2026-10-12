/**
 * Distributed Manta Ray Foraging Optimization (MRFO) Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired Mobula birostris collective feeding dynamics:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations, N manta rays, and n cities.
 * - Strategy 1: Chain Foraging: Manta rays align head-to-tail into coordinated foraging lines, tracking both the leader ray and the plankton center.
 * - Strategy 2: Cyclone Foraging: Rays form spiral vortexes moving towards dense plankton concentrations, balancing exploration and exploitation.
 * - Strategy 3: Somersault Foraging: Rays perform acrobatic somersaults around the plankton pivot, jumping to unexplored search spaces.
 * - Discrete combinatorial operators: Order Crossover (OX), Cyclical segment inversion, Pivot reflection, and 2-Opt local search refinement.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface MRFOTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedMantaRayForagingOptimizationTSPOptimizer {
    private points: Point2D[] = [];

    constructor() {}

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

    private twoOpt(tourIndices: number[]): number[] {
        const n = tourIndices.length;
        if (n < 4) return [...tourIndices];

        let best = [...tourIndices];
        let bestCost = this.computeTourCost(best);
        let improved = true;
        let passes = 0;

        while (improved && passes < 50) {
            improved = false;
            passes++;
            for (let i = 0; i < n - 1; i++) {
                for (let j = i + 2; j < n; j++) {
                    if (i === 0 && j === n - 1) continue;
                    const candidate = [
                        ...best.slice(0, i + 1),
                        ...best.slice(i + 1, j + 1).reverse(),
                        ...best.slice(j + 1)
                    ];
                    const candCost = this.computeTourCost(candidate);
                    if (candCost < bestCost - 1e-9) {
                        best = candidate;
                        bestCost = candCost;
                        improved = true;
                        break;
                    }
                }
                if (improved) break;
            }
        }
        return best;
    }

    private orderCrossover(parent1: number[], parent2: number[], start: number, end: number): number[] {
        const n = parent1.length;
        const child: number[] = new Array(n).fill(-1);
        const [s, e] = start <= end ? [start, end] : [end, start];

        const segment = new Set<number>();
        for (let i = s; i <= e; i++) {
            child[i] = parent1[i];
            segment.add(parent1[i]);
        }

        let p2Idx = 0;
        for (let i = 0; i < n; i++) {
            if (i >= s && i <= e) continue;
            while (p2Idx < n && segment.has(parent2[p2Idx])) {
                p2Idx++;
            }
            if (p2Idx < n) {
                child[i] = parent2[p2Idx];
                p2Idx++;
            }
        }
        return child;
    }

    private chainForaging(current: number[], prev: number[], best: number[], prng: () => number): number[] {
        const n = current.length;
        if (n < 4) return [...current];

        // Combine subtour features from the ray in front (prev) and the plankton center (best)
        const cut1 = Math.floor(prng() * n);
        const cut2 = Math.floor(prng() * n);
        const child = this.orderCrossover(best, current, cut1, cut2);

        // Small local adjustment towards preceding ray
        if (prng() < 0.3) {
            const idx1 = Math.floor(prng() * n);
            const idx2 = (idx1 + 1) % n;
            const tmp = child[idx1];
            child[idx1] = child[idx2];
            child[idx2] = tmp;
        }

        return child;
    }

    private cycloneForaging(current: number[], best: number[], iterRatio: number, prng: () => number): number[] {
        const n = current.length;
        if (n < 4) return [...current];

        // Spiral vortex: reverse a spiral arc of vertices
        const arcLength = Math.max(2, Math.floor((1 - iterRatio * 0.5) * (n / 2) * prng() + 2));
        const start = Math.floor(prng() * n);
        const copy = [...current];

        const candidate = this.orderCrossover(best, copy, start, (start + arcLength) % n);
        return candidate;
    }

    private somersaultForaging(current: number[], best: number[], prng: () => number): number[] {
        const n = current.length;
        if (n < 4) return [...current];

        // Acrobatic backward pivot somersault around the plankton center
        const copy = [...current];
        const pivot = Math.floor(prng() * (n - 2));
        const len = 2 + Math.floor(prng() * Math.min(4, n - pivot));
        const sub = copy.slice(pivot, pivot + len).reverse();
        copy.splice(pivot, len, ...sub);

        return this.orderCrossover(best, copy, pivot, Math.min(n - 1, pivot + len));
    }

    public search(maxIterations = 120, populationSize = 25, seed = 73): MRFOTSPResult {
        const n = this.points.length;
        if (n === 0) {
            return {
                found: false,
                initialCost: 0,
                bestCost: 0,
                tour: [],
                iterationsCompleted: 0
            };
        }

        if (n === 1) {
            return {
                found: true,
                initialCost: 0,
                bestCost: 0,
                tour: [this.points[0].id, this.points[0].id],
                iterationsCompleted: 0
            };
        }

        if (n === 2) {
            const cost = this.getDistance(this.points[0], this.points[1]) * 2;
            return {
                found: true,
                initialCost: cost,
                bestCost: cost,
                tour: [this.points[0].id, this.points[1].id, this.points[0].id],
                iterationsCompleted: 0
            };
        }

        // LCG PRNG for deterministic reproducibility
        let s = seed >>> 0;
        const prng = (): number => {
            s = (s * 1664525 + 1013904223) >>> 0;
            return s / 4294967296;
        };

        const popSize = Math.max(10, populationSize);
        let population: number[][] = [];

        // Nearest neighbor baseline
        const nnTour = this.buildNearestNeighborTour();
        population.push(nnTour);

        // Randomly initialized manta rays
        const baseIndices = Array.from({ length: n }, (_, i) => i);
        for (let i = 1; i < popSize; i++) {
            const shuffled = [...baseIndices];
            for (let j = n - 1; j > 0; j--) {
                const k = Math.floor(prng() * (j + 1));
                [shuffled[j], shuffled[k]] = [shuffled[k], shuffled[j]];
            }
            population.push(shuffled);
        }

        // Identify initial best plankton patch
        let bestTour = [...population[0]];
        let bestCost = this.computeTourCost(bestTour);
        const initialCost = bestCost;

        for (let i = 1; i < popSize; i++) {
            const cost = this.computeTourCost(population[i]);
            if (cost < bestCost) {
                bestCost = cost;
                bestTour = [...population[i]];
            }
        }

        // Main MRFO Iteration Loop
        for (let iter = 0; iter < maxIterations; iter++) {
            const iterRatio = iter / maxIterations;
            const newPopulation: number[][] = [];

            for (let i = 0; i < popSize; i++) {
                const current = population[i];
                const prev = i === 0 ? population[popSize - 1] : population[i - 1];
                let step: number[];

                const strategyRoll = prng();
                if (strategyRoll < 0.5) {
                    // Cyclone foraging if random parameter < 0.5
                    if (prng() < 0.5) {
                        step = this.cycloneForaging(current, bestTour, iterRatio, prng);
                    } else {
                        // Chain foraging
                        step = this.chainForaging(current, prev, bestTour, prng);
                    }
                } else {
                    // Somersault foraging around the plankton center
                    step = this.somersaultForaging(current, bestTour, prng);
                }

                const stepCost = this.computeTourCost(step);
                const currCost = this.computeTourCost(current);

                if (stepCost < currCost) {
                    newPopulation.push(step);
                    if (stepCost < bestCost) {
                        bestCost = stepCost;
                        bestTour = [...step];
                    }
                } else {
                    newPopulation.push(current);
                }
            }

            population = newPopulation;
        }

        // 2-Opt local search refinement on final best tour
        bestTour = this.twoOpt(bestTour);
        bestCost = this.computeTourCost(bestTour);

        const tourIds = bestTour.map(idx => this.points[idx].id);
        tourIds.push(tourIds[0]);

        return {
            found: true,
            initialCost,
            bestCost,
            tour: tourIds,
            iterationsCompleted: maxIterations
        };
    }

    private buildNearestNeighborTour(): number[] {
        const n = this.points.length;
        const unvisited = new Set<number>();
        for (let i = 1; i < n; i++) unvisited.add(i);

        const tour = [0];
        let current = 0;

        while (unvisited.size > 0) {
            let nearest = -1;
            let minDist = Infinity;

            for (const candidate of unvisited) {
                const dist = this.getDistance(this.points[current], this.points[candidate]);
                if (dist < minDist) {
                    minDist = dist;
                    nearest = candidate;
                }
            }

            unvisited.delete(nearest);
            tour.push(nearest);
            current = nearest;
        }

        return tour;
    }
}
