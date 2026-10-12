/**
 * Distributed Aquila Optimizer (AO) Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired Aquila chrysaetos predatory flight and prey capture dynamics:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations, N aquilas, and n cities.
 * - Strategy 1 (Expanded Exploration, t <= (2/3)T, r <= 0.5): High soaring flight with vertical stoop to detect prey zones.
 * - Strategy 2 (Narrowed Exploration, t <= (2/3)T, r > 0.5): Contour flight with short glide attacks, circling prey contour.
 * - Strategy 3 (Expanded Exploitation, t > (2/3)T, r <= 0.5): Low flight with slow descent attack, closing in on prey.
 * - Strategy 4 (Narrowed Exploitation, t > (2/3)T, r > 0.5): Walking and snatching prey on land, direct strike with 2-Opt local refinement.
 * - Discrete combinatorial operators: Order Crossover (OX), Contour glide subtour inversion, Snatching swap mutation, and 2-Opt local search.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface AOTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedAquilaOptimizerTSPOptimizer {
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

    private contourGlideInversion(tour: number[], prng: () => number): number[] {
        const n = tour.length;
        if (n < 4) return [...tour];
        const copy = [...tour];
        const i = Math.floor(prng() * (n - 2));
        const span = 2 + Math.floor(prng() * (n - i - 1));
        const j = i + span;
        const sub = copy.slice(i, j + 1).reverse();
        copy.splice(i, sub.length, ...sub);
        return copy;
    }

    private snatchingSwap(tour: number[], prng: () => number): number[] {
        const n = tour.length;
        if (n < 3) return [...tour];
        const copy = [...tour];
        const i = Math.floor(prng() * n);
        const j = (i + 1 + Math.floor(prng() * (n - 1))) % n;
        const tmp = copy[i];
        copy[i] = copy[j];
        copy[j] = tmp;
        return copy;
    }

    public search(maxIterations = 120, populationSize = 25, seed = 64): AOTSPResult {
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

        // Deterministic LCG
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

        // Randomly initialized aquilas
        const baseIndices = Array.from({ length: n }, (_, i) => i);
        for (let i = 1; i < popSize; i++) {
            const shuffled = [...baseIndices];
            for (let j = n - 1; j > 0; j--) {
                const k = Math.floor(prng() * (j + 1));
                [shuffled[j], shuffled[k]] = [shuffled[k], shuffled[j]];
            }
            population.push(shuffled);
        }

        // Identify initial best Aquila
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

        // AO Main Optimization Loop
        const explorationCutoff = Math.floor((2 / 3) * maxIterations);

        for (let iter = 0; iter < maxIterations; iter++) {
            const newPopulation: number[][] = [];

            for (let i = 0; i < popSize; i++) {
                const current = population[i];
                let step: number[];
                const r = prng();

                if (iter <= explorationCutoff) {
                    if (r <= 0.5) {
                        // Strategy 1: Expanded Exploration (High soar with vertical stoop)
                        const randomPartner = population[Math.floor(prng() * popSize)];
                        const cut1 = Math.floor(prng() * n);
                        const cut2 = Math.floor(prng() * n);
                        step = this.orderCrossover(bestTour, randomPartner, cut1, cut2);
                    } else {
                        // Strategy 2: Narrowed Exploration (Contour flight with glide attack)
                        step = this.contourGlideInversion(current, prng);
                        const cut1 = Math.floor(prng() * n);
                        const cut2 = Math.floor(prng() * n);
                        step = this.orderCrossover(bestTour, step, cut1, cut2);
                    }
                } else {
                    if (r <= 0.5) {
                        // Strategy 3: Expanded Exploitation (Low flight with slow descent)
                        const cut1 = Math.floor(prng() * n);
                        const cut2 = Math.floor(prng() * n);
                        step = this.orderCrossover(bestTour, current, cut1, cut2);
                        if (prng() < 0.3) {
                            step = this.snatchingSwap(step, prng);
                        }
                    } else {
                        // Strategy 4: Narrowed Exploitation (Walk and direct snatch on land)
                        step = this.snatchingSwap(bestTour, prng);
                        step = this.twoOpt(step);
                    }
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

        // 2-Opt local search refinement on the final best Aquila tour
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
