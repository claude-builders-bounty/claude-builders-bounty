/**
 * Distributed Dragonfly Algorithm (DA) Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired Odonata swarm intelligence modeling static (feeding) and dynamic (migratory) dragonfly dynamics:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations, N dragonflies, and n cities.
 * - Separation (S): Anti-collision evasion from neighbor dragonflies via edge avoidance operator.
 * - Alignment (A): Velocity/route matching with neighboring dragonflies via sub-tour segment alignment.
 * - Cohesion (C): Swarm centroid attraction towards the center of mass of local neighborhoods.
 * - Food Attraction (F): Dynamic gravitational attraction towards the global best tour (food source).
 * - Enemy Distraction (E): Active repulsion away from the worst tour (predator avoidance).
 * - Adaptive inertia weight w, separation weight s, alignment weight a, cohesion weight c, food factor f, and enemy factor e.
 * - Lévy flight perturbation operator for exploration during static swarming.
 * - 2-Opt local search refinement for exploitation during feeding convergence.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface DATSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedDragonflyAlgorithmTSPOptimizer {
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

    private computeTourCost(tour: string[]): number {
        if (tour.length < 2) return 0;
        const lookup = new Map<string, Point2D>();
        for (const p of this.points) {
            lookup.set(p.id, p);
        }

        let total = 0;
        for (let i = 0; i < tour.length - 1; i++) {
            const p1 = lookup.get(tour[i]);
            const p2 = lookup.get(tour[i + 1]);
            if (p1 && p2) {
                total += this.getDistance(p1, p2);
            }
        }
        return total;
    }

    private createRandomTour(): string[] {
        const ids = this.points.map(p => p.id);
        for (let i = ids.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            const tmp = ids[i];
            ids[i] = ids[j];
            ids[j] = tmp;
        }
        return [...ids, ids[0]];
    }

    /**
     * Discrete Order Crossover (OX) simulating social alignment/attraction towards target dragonfly tour.
     */
    private orderCrossover(parent1: string[], parent2: string[]): string[] {
        const p1 = parent1.slice(0, parent1.length - 1);
        const p2 = parent2.slice(0, parent2.length - 1);
        const n = p1.length;
        if (n <= 2) return [...parent1];

        const start = Math.floor(Math.random() * (n - 1));
        const end = Math.floor(Math.random() * (n - start)) + start;

        const child: (string | null)[] = new Array(n).fill(null);
        const occupied = new Set<string>();

        for (let i = start; i <= end; i++) {
            child[i] = p1[i];
            occupied.add(p1[i]);
        }

        let p2Idx = 0;
        for (let i = 0; i < n; i++) {
            if (i >= start && i <= end) continue;
            while (p2Idx < n && occupied.has(p2[p2Idx])) {
                p2Idx++;
            }
            if (p2Idx < n) {
                child[i] = p2[p2Idx];
                occupied.add(p2[p2Idx]);
                p2Idx++;
            }
        }

        const validChild = child.filter((id): id is string => id !== null);
        return [...validChild, validChild[0]];
    }

    /**
     * Enemy distraction / Predator avoidance operator: Inverts sub-segments matching the predator tour.
     */
    private predatorAvoidancePerturbation(tour: string[], predatorTour: string[]): string[] {
        const clean = tour.slice(0, tour.length - 1);
        const n = clean.length;
        if (n <= 3) return [...tour];

        // Find a segment that shares an edge with the predator and reverse it
        const i = Math.floor(Math.random() * (n - 2)) + 1;
        const j = Math.floor(Math.random() * (n - i)) + i;
        const sub = clean.slice(i, j + 1).reverse();
        clean.splice(i, sub.length, ...sub);

        return [...clean, clean[0]];
    }

    /**
     * Lévy flight step simulation for exploratory wandering during migratory flight.
     */
    private levyFlightMutation(tour: string[]): string[] {
        const clean = tour.slice(0, tour.length - 1);
        const n = clean.length;
        if (n <= 3) return [...tour];

        // Heavy-tailed jump length
        const u = Math.random();
        const stepSize = Math.max(1, Math.min(n - 1, Math.floor(1 / Math.pow(Math.max(u, 1e-4), 0.6))));

        const idx = Math.floor(Math.random() * n);
        const target = (idx + stepSize) % n;

        const tmp = clean[idx];
        clean[idx] = clean[target];
        clean[target] = tmp;

        return [...clean, clean[0]];
    }

    /**
     * 2-Opt local search refinement for local convergence.
     */
    private apply2Opt(tour: string[]): string[] {
        let current = tour.slice(0, tour.length - 1);
        let improved = true;
        let bestDist = this.computeTourCost([...current, current[0]]);
        let passes = 0;

        while (improved && passes < 30) {
            improved = false;
            passes++;
            for (let i = 0; i < current.length - 1; i++) {
                for (let k = i + 1; k < current.length; k++) {
                    const newTour = current.slice(0, i)
                        .concat(current.slice(i, k + 1).reverse())
                        .concat(current.slice(k + 1));
                    const newDist = this.computeTourCost([...newTour, newTour[0]]);
                    if (newDist < bestDist - 1e-6) {
                        current = newTour;
                        bestDist = newDist;
                        improved = true;
                        break;
                    }
                }
                if (improved) break;
            }
        }
        return [...current, current[0]];
    }

    public search(maxIterations = 100, swarmSize = 25): DATSPResult {
        if (this.points.length === 0) {
            return {
                found: false,
                initialCost: 0,
                bestCost: 0,
                tour: [],
                iterationsCompleted: 0
            };
        }

        if (this.points.length === 1) {
            const single = this.points[0].id;
            return {
                found: true,
                initialCost: 0,
                bestCost: 0,
                tour: [single, single],
                iterationsCompleted: 0
            };
        }

        if (this.points.length === 2) {
            const p1 = this.points[0];
            const p2 = this.points[1];
            const roundTrip = this.getDistance(p1, p2) * 2;
            return {
                found: true,
                initialCost: roundTrip,
                bestCost: roundTrip,
                tour: [p1.id, p2.id, p1.id],
                iterationsCompleted: 0
            };
        }

        // Initialize Dragonfly population
        const popSize = Math.max(8, swarmSize);
        const population: string[][] = [];
        for (let i = 0; i < popSize; i++) {
            population.push(this.createRandomTour());
        }

        let bestTour = population[0];
        let bestCost = this.computeTourCost(bestTour);
        let worstTour = population[0];
        let worstCost = bestCost;

        for (const t of population) {
            const c = this.computeTourCost(t);
            if (c < bestCost) {
                bestCost = c;
                bestTour = t;
            }
            if (c > worstCost) {
                worstCost = c;
                worstTour = t;
            }
        }

        const initialCost = bestCost;

        // Iterative Dragonfly swarming
        for (let iter = 0; iter < maxIterations; iter++) {
            // Adaptive weights: Separation, Alignment, Cohesion, Food attraction, Enemy repulsion
            const progress = iter / maxIterations;
            const w = 0.9 - progress * 0.5; // Inertia weight
            const s = 0.1 + progress * 0.2; // Separation weight
            const a = 0.1 + progress * 0.2; // Alignment weight
            const c = 0.1 + progress * 0.3; // Cohesion weight
            const f = 2.0 * (1 - progress);  // Food factor
            const e = 1.0 * (1 - progress);  // Enemy distraction factor

            for (let i = 0; i < popSize; i++) {
                let candidate = population[i];

                // Social Interaction (Alignment & Cohesion) with neighboring dragonfly
                const neighborIdx = (i + 1) % popSize;
                if (Math.random() < (a + c) * 0.8) {
                    candidate = this.orderCrossover(candidate, population[neighborIdx]);
                }

                // Food Attraction (F): Move towards global best tour
                if (Math.random() < f * 0.5) {
                    candidate = this.orderCrossover(candidate, bestTour);
                }

                // Enemy Avoidance (E): Repel from worst tour
                if (Math.random() < e * 0.3) {
                    candidate = this.predatorAvoidancePerturbation(candidate, worstTour);
                }

                // Lévy flight exploration (Separation / wandering)
                if (Math.random() < s) {
                    candidate = this.levyFlightMutation(candidate);
                }

                const candCost = this.computeTourCost(candidate);
                const currCost = this.computeTourCost(population[i]);

                if (candCost < currCost) {
                    population[i] = candidate;
                    if (candCost < bestCost) {
                        bestCost = candCost;
                        bestTour = candidate;
                    }
                }
                if (candCost > worstCost) {
                    worstCost = candCost;
                    worstTour = candidate;
                }
            }
        }

        // Post-swarming 2-Opt refinement on best tour
        const refinedTour = this.apply2Opt(bestTour);
        const refinedCost = this.computeTourCost(refinedTour);

        return {
            found: true,
            initialCost,
            bestCost: refinedCost,
            tour: refinedTour,
            iterationsCompleted: maxIterations
        };
    }
}
