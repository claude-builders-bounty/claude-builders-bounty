/**
 * Distributed Mountain Gazelle Optimizer (MGO) Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired Gazella gazella social foraging and anti-predator pronking dynamics:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations, N gazelles, and n cities.
 * - Strategy 1: Territorial Solitary Males (TSM) - Dominant male territory defense and long-range exploration.
 * - Strategy 2: Bachelor Male Herds (BMH) - Young male cooperative social foraging and sparring interactions.
 * - Strategy 3: Maternity Herds (MH) - Protective female/fawn grazing exploitation around the safest fertile grounds.
 * - Strategy 4: Migration & Pronking Escape - High-speed stotting leaps and evasive trajectory shifts to avoid predators.
 * - Discrete combinatorial operators: Order Crossover (OX), Pronking segment reversal, Sparring vertex swaps, and 2-Opt local search.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface MGOTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedMountainGazelleOptimizerTSPOptimizer {
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

    private pronkingLeap(tour: number[], prng: () => number): number[] {
        const n = tour.length;
        if (n < 4) return [...tour];
        // High-speed stotting leap: reverse a random subtour
        const copy = [...tour];
        const i = Math.floor(prng() * (n - 2));
        const span = 2 + Math.floor(prng() * (n - i - 1));
        const j = i + span;
        const sub = copy.slice(i, j + 1).reverse();
        copy.splice(i, sub.length, ...sub);
        return copy;
    }

    private sparringSwap(tour: number[], prng: () => number): number[] {
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

    public search(maxIterations = 120, populationSize = 25, seed = 88): MGOTSPResult {
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

        // Nearest neighbor baseline individual
        const nnTour = this.buildNearestNeighborTour();
        population.push(nnTour);

        // Randomly initialized gazelles
        const baseIndices = Array.from({ length: n }, (_, i) => i);
        for (let i = 1; i < popSize; i++) {
            const shuffled = [...baseIndices];
            for (let j = n - 1; j > 0; j--) {
                const k = Math.floor(prng() * (j + 1));
                [shuffled[j], shuffled[k]] = [shuffled[k], shuffled[j]];
            }
            population.push(shuffled);
        }

        // Identify initial territorial male (best individual)
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

        // Main MGO Optimization Loop
        for (let iter = 0; iter < maxIterations; iter++) {
            const newPopulation: number[][] = [];

            for (let i = 0; i < popSize; i++) {
                const current = population[i];
                let step: number[];

                const socialRoll = prng();
                if (socialRoll < 0.3) {
                    // Strategy 1: Territorial Solitary Male (exploration)
                    const cut1 = Math.floor(prng() * n);
                    const cut2 = Math.floor(prng() * n);
                    step = this.orderCrossover(bestTour, current, cut1, cut2);
                } else if (socialRoll < 0.6) {
                    // Strategy 2: Bachelor Male Herd (sparring)
                    const partnerIdx = Math.floor(prng() * popSize);
                    const partner = population[partnerIdx];
                    const cut1 = Math.floor(prng() * n);
                    const cut2 = Math.floor(prng() * n);
                    step = this.orderCrossover(partner, current, cut1, cut2);
                    if (prng() < 0.4) {
                        step = this.sparringSwap(step, prng);
                    }
                } else if (socialRoll < 0.85) {
                    // Strategy 3: Maternity Herd (grazing exploitation around best ground)
                    step = this.pronkingLeap(bestTour, prng);
                    const cut1 = Math.floor(prng() * n);
                    const cut2 = Math.floor(prng() * n);
                    step = this.orderCrossover(bestTour, step, cut1, cut2);
                } else {
                    // Strategy 4: Migration & Pronking Escape (predator avoidance)
                    step = this.pronkingLeap(current, prng);
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

        // 2-Opt local search refinement on the final best gazelle tour
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
