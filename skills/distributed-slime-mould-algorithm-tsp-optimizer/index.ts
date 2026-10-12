/**
 * Distributed Slime Mould Algorithm (SMA) Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired plasmodial foraging of Physarum polycephalum (slime mould):
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations, N slime mould biomass nodes, and n cities.
 * - Simulates positive/negative bio-feedback oscillatory contractions of venous tubes based on food concentration.
 * - Dynamic feedback weight W(i) modulates venous thickness, accelerating flow along high-yield transport corridors.
 * - Exploratory random search threshold z simulates amoeboid pseudopod expansion into unexplored topological domains.
 * - Order Crossover (OX) guided by global high-nutrient food odor source (best tour) and neighboring biomass veins.
 * - 2-Opt local search refinement for post-foraging venous tube network convergence.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface SMATSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedSlimeMouldAlgorithmTSPOptimizer {
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
     * Discrete Order Crossover (OX) simulating cytoplasmic flow along thickened venous channels.
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
     * Amoeboid pseudopod exploration: Heavy perturbation simulating protoplasmic branching.
     */
    private pseudopodBranchingPerturbation(tour: string[]): string[] {
        const clean = tour.slice(0, tour.length - 1);
        const n = clean.length;
        if (n <= 3) return [...tour];

        const i = Math.floor(Math.random() * (n - 2)) + 1;
        const j = Math.min(n - 1, i + Math.floor(Math.random() * (n / 2)) + 1);
        const sub = clean.slice(i, j + 1).reverse();
        clean.splice(i, sub.length, ...sub);

        return [...clean, clean[0]];
    }

    /**
     * 2-Opt local search refinement for venous network stabilization.
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

    public search(maxIterations = 100, populationSize = 25): SMATSPResult {
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

        const size = Math.max(8, populationSize);
        let population: string[][] = [];
        for (let i = 0; i < size; i++) {
            population.push(this.createRandomTour());
        }

        let bestTour = population[0];
        let bestCost = this.computeTourCost(bestTour);

        for (const t of population) {
            const c = this.computeTourCost(t);
            if (c < bestCost) {
                bestCost = c;
                bestTour = t;
            }
        }

        const initialCost = bestCost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Sort population by fitness (shorter distance = better food concentration)
            population.sort((a, b) => this.computeTourCost(a) - this.computeTourCost(b));
            bestTour = population[0];
            bestCost = this.computeTourCost(bestTour);
            const worstCost = this.computeTourCost(population[population.length - 1]);

            // Oscillation parameter a = arctanh(-(iter / maxIterations) + 1)
            const progress = iter / maxIterations;
            const a = Math.atanh(Math.max(-0.99, Math.min(0.99, -(progress) + 1)));

            for (let i = 0; i < size; i++) {
                const p = Math.random();
                const z = 0.03; // Exploration threshold for amoeboid expansion

                let candidate = population[i];

                if (p < z) {
                    // Random pseudopod expansion
                    candidate = this.createRandomTour();
                } else {
                    // Venous contracting update
                    const r = Math.random();
                    const fitness = this.computeTourCost(population[i]);
                    const diff = Math.max(1e-6, worstCost - bestCost);
                    // Biomass weight W
                    const w = i < size / 2 
                        ? 1 + r * Math.log10((worstCost - fitness) / diff + 1)
                        : 1 - r * Math.log10((worstCost - fitness) / diff + 1);

                    const pA = Math.floor(Math.random() * size);
                    const pB = Math.floor(Math.random() * size);

                    if (r < 0.5) {
                        // Forward cytoplasmic flow towards food concentration (best tour)
                        candidate = this.orderCrossover(candidate, bestTour);
                        if (w > 1.2) {
                            candidate = this.pseudopodBranchingPerturbation(candidate);
                        }
                    } else {
                        // Venous interaction between dual biomass regions
                        candidate = this.orderCrossover(population[pA], population[pB]);
                    }
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
            }
        }

        // Post-foraging 2-Opt local refinement on best tour
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
