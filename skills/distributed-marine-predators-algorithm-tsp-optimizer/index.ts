/**
 * Distributed Marine Predators Algorithm (MPA) Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired marine predator foraging strategy based on Lévy flight and Brownian motion dynamics:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations, N marine predators, and n cities.
 * - Phase 1 (High velocity ratio, t < Max_Iter/3): Exploration phase where prey moves faster than predator (Brownian motion of prey).
 * - Phase 2 (Unit velocity ratio, Max_Iter/3 <= t < 2*Max_Iter/3): Transition phase (Predator Brownian exploration, Prey Lévy exploitation).
 * - Phase 3 (Low velocity ratio, t >= 2*Max_Iter/3): Exploitation phase where predator exhibits Lévy flight pursuit.
 * - FADs effect (Fish Aggregating Devices): Environmental eddy perturbations and vortex-induced long jumps.
 * - Discrete combinatorial operators: Subtour Order Crossover (OX), Scramble mutation, and 2-Opt local search.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface MPATSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedMarinePredatorsAlgorithmTSPOptimizer {
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
                    // Candidate 2-opt swap
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

    private brownianStep(tour: number[], prng: () => number): number[] {
        const n = tour.length;
        if (n < 3) return [...tour];
        // Short-range swap simulating Brownian dispersion
        const copy = [...tour];
        const idx1 = Math.floor(prng() * n);
        const idx2 = (idx1 + 1 + Math.floor(prng() * 2)) % n;
        const tmp = copy[idx1];
        copy[idx1] = copy[idx2];
        copy[idx2] = tmp;
        return copy;
    }

    private levyFlightStep(tour: number[], prng: () => number): number[] {
        const n = tour.length;
        if (n < 4) return [...tour];
        // Heavy-tailed jump: reverse a randomly sized subtour
        const copy = [...tour];
        const i = Math.floor(prng() * (n - 2));
        const span = 2 + Math.floor(prng() * (n - i - 1));
        const j = i + span;
        const reversed = copy.slice(i, j + 1).reverse();
        copy.splice(i, reversed.length, ...reversed);
        return copy;
    }

    private applyFADsEffect(tour: number[], prng: () => number, fadsProb = 0.2): number[] {
        if (prng() > fadsProb || tour.length < 4) return [...tour];
        // Whirlpool / eddy perturbation: scramble a small slice of tour
        const n = tour.length;
        const copy = [...tour];
        const start = Math.floor(prng() * (n - 2));
        const len = Math.min(3, n - start);
        const sub = copy.slice(start, start + len);
        // Fisher-Yates shuffle on the slice
        for (let i = sub.length - 1; i > 0; i--) {
            const j = Math.floor(prng() * (i + 1));
            [sub[i], sub[j]] = [sub[j], sub[i]];
        }
        copy.splice(start, len, ...sub);
        return copy;
    }

    public search(maxIterations = 100, populationSize = 25, seed = 42): MPATSPResult {
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

        // Linear Congruential Generator (LCG) for deterministic reproducibility
        let s = seed >>> 0;
        const prng = (): number => {
            s = (s * 1664525 + 1013904223) >>> 0;
            return s / 4294967296;
        };

        // Initialize Predator & Prey population
        const popSize = Math.max(10, populationSize);
        let population: number[][] = [];

        // Nearest neighbor baseline individual
        const nnTour = this.buildNearestNeighborTour();
        population.push(nnTour);

        // Randomly initialized predators
        const baseIndices = Array.from({ length: n }, (_, i) => i);
        for (let i = 1; i < popSize; i++) {
            const shuffled = [...baseIndices];
            for (let j = n - 1; j > 0; j--) {
                const k = Math.floor(prng() * (j + 1));
                [shuffled[j], shuffled[k]] = [shuffled[k], shuffled[j]];
            }
            population.push(shuffled);
        }

        // Evaluate initial best (Top Predator Elite)
        let eliteTour = [...population[0]];
        let eliteCost = this.computeTourCost(eliteTour);
        const initialCost = eliteCost;

        for (let i = 1; i < popSize; i++) {
            const cost = this.computeTourCost(population[i]);
            if (cost < eliteCost) {
                eliteCost = cost;
                eliteTour = [...population[i]];
            }
        }

        // Marine Predators Algorithm Iteration Loop
        const phase1Bound = Math.floor(maxIterations / 3);
        const phase2Bound = Math.floor((2 * maxIterations) / 3);

        for (let iter = 0; iter < maxIterations; iter++) {
            const newPopulation: number[][] = [];

            for (let i = 0; i < popSize; i++) {
                let current = population[i];
                let step: number[];

                if (iter < phase1Bound) {
                    // Phase 1: High velocity ratio (Prey Brownian motion)
                    step = this.brownianStep(current, prng);
                    // Order crossover guided by Elite Predator
                    const pt1 = Math.floor(prng() * n);
                    const pt2 = Math.floor(prng() * n);
                    step = this.orderCrossover(eliteTour, step, pt1, pt2);
                } else if (iter < phase2Bound) {
                    // Phase 2: Unit velocity ratio (Intermediate transition)
                    if (i < popSize / 2) {
                        // First half: Predator explores via Brownian motion
                        step = this.brownianStep(eliteTour, prng);
                    } else {
                        // Second half: Prey exploits via Lévy flight
                        step = this.levyFlightStep(current, prng);
                        const pt1 = Math.floor(prng() * n);
                        const pt2 = Math.floor(prng() * n);
                        step = this.orderCrossover(step, eliteTour, pt1, pt2);
                    }
                } else {
                    // Phase 3: Low velocity ratio (Predator Lévy flight pursuit)
                    step = this.levyFlightStep(eliteTour, prng);
                    const pt1 = Math.floor(prng() * n);
                    const pt2 = Math.floor(prng() * n);
                    step = this.orderCrossover(eliteTour, step, pt1, pt2);
                }

                // Fish Aggregating Devices (FADs) eddy effect
                step = this.applyFADsEffect(step, prng);

                // Memory matrix replacement policy
                const stepCost = this.computeTourCost(step);
                const currCost = this.computeTourCost(current);

                if (stepCost < currCost) {
                    newPopulation.push(step);
                    if (stepCost < eliteCost) {
                        eliteCost = stepCost;
                        eliteTour = [...step];
                    }
                } else {
                    newPopulation.push(current);
                }
            }

            population = newPopulation;
        }

        // 2-Opt local search refinement on the final elite predator tour
        eliteTour = this.twoOpt(eliteTour);
        eliteCost = this.computeTourCost(eliteTour);

        const tourIds = eliteTour.map(idx => this.points[idx].id);
        tourIds.push(tourIds[0]); // Closed cycle

        return {
            found: true,
            initialCost,
            bestCost: eliteCost,
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
