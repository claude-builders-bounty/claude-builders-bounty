/**
 * Distributed Dung Beetle Optimizer (DBO) Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired collective behavioral intelligence of Scarabaeinae (dung beetles):
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations, N beetles, and n cities.
 * - 4-Subpopulation Division:
 *   1. Ball-Rolling Beetles: Celestial polarization navigation pushing toward best global solutions, executing dance reorientation upon encountering obstacles.
 *   2. Breeding Ball Beetles: Dynamic safe boundary oviposition modeling reproductive egg balls in fertile sub-regions.
 *   3. Small Foraging Beetles: Multidirectional localized exploration in optimal feeding patches.
 *   4. Stealing Beetles: Opportunistic thievery raiding best-quality dung balls from peer beetles.
 * - Order Crossover (OX) for rolling navigation and stealing interception.
 * - Dancing reorientation operator via localized sub-tour inversion.
 * - 2-Opt local search refinement for post-foraging tour convergence.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface DBOTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedDungBeetleOptimizerTSPOptimizer {
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
     * Discrete Order Crossover (OX) simulating ball rolling / stealing alignment.
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
     * Dancing reorientation operator: Beetle climbs on dung ball and rotates to acquire new celestial compass heading.
     */
    private dancingReorientation(tour: string[]): string[] {
        const clean = tour.slice(0, tour.length - 1);
        const n = clean.length;
        if (n <= 3) return [...tour];

        // Invert subsegment to simulate 180 or 90 degree dance turn
        const i = Math.floor(Math.random() * (n - 2)) + 1;
        const j = Math.min(n - 1, i + Math.floor(Math.random() * 3) + 1);
        const sub = clean.slice(i, j + 1).reverse();
        clean.splice(i, sub.length, ...sub);

        return [...clean, clean[0]];
    }

    /**
     * Local foraging perturbation: Minor single-pair city exchange simulating small beetle browsing.
     */
    private localForagingPerturbation(tour: string[]): string[] {
        const clean = tour.slice(0, tour.length - 1);
        const n = clean.length;
        if (n <= 3) return [...tour];

        const i = Math.floor(Math.random() * n);
        const j = (i + 1 + Math.floor(Math.random() * 2)) % n;
        const tmp = clean[i];
        clean[i] = clean[j];
        clean[j] = tmp;

        return [...clean, clean[0]];
    }

    /**
     * 2-Opt local search refinement for post-foraging tour convergence.
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

    public search(maxIterations = 100, populationSize = 24): DBOTSPResult {
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

        const size = Math.max(12, populationSize);
        const population: string[][] = [];
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

        // Subpopulation partition proportions:
        // 1. Rolling beetles: ~25%
        // 2. Breeding beetles: ~25%
        // 3. Foraging beetles: ~25%
        // 4. Stealing beetles: ~25%
        const quarter = Math.floor(size / 4);

        for (let iter = 0; iter < maxIterations; iter++) {
            // Sort population by cost ascending
            population.sort((a, b) => this.computeTourCost(a) - this.computeTourCost(b));
            bestTour = population[0];
            bestCost = this.computeTourCost(bestTour);

            // 1. Ball-Rolling Beetles (indices 0 to quarter - 1)
            for (let i = 0; i < quarter; i++) {
                let candidate = population[i];
                if (Math.random() < 0.7) {
                    // Straight-line rolling guided by sunlight/best tour
                    candidate = this.orderCrossover(candidate, bestTour);
                } else {
                    // Obstacle encountered -> Dancing on ball
                    candidate = this.dancingReorientation(candidate);
                }

                const candCost = this.computeTourCost(candidate);
                if (candCost < this.computeTourCost(population[i])) {
                    population[i] = candidate;
                }
            }

            // 2. Breeding Beetles (indices quarter to 2 * quarter - 1)
            for (let i = quarter; i < 2 * quarter; i++) {
                let candidate = population[i];
                // Oviposition safe zone crossover with peer breeding beetle
                const peer = population[quarter + Math.floor(Math.random() * quarter)];
                candidate = this.orderCrossover(candidate, peer);
                if (Math.random() < 0.4) {
                    candidate = this.dancingReorientation(candidate);
                }

                const candCost = this.computeTourCost(candidate);
                if (candCost < this.computeTourCost(population[i])) {
                    population[i] = candidate;
                }
            }

            // 3. Small Foraging Beetles (indices 2 * quarter to 3 * quarter - 1)
            for (let i = 2 * quarter; i < 3 * quarter; i++) {
                let candidate = population[i];
                // Local foraging in feeding grounds
                candidate = this.localForagingPerturbation(candidate);
                if (Math.random() < 0.5) {
                    candidate = this.orderCrossover(candidate, bestTour);
                }

                const candCost = this.computeTourCost(candidate);
                if (candCost < this.computeTourCost(population[i])) {
                    population[i] = candidate;
                }
            }

            // 4. Stealing Beetles (indices 3 * quarter to size - 1)
            for (let i = 3 * quarter; i < size; i++) {
                let candidate = population[i];
                // Target an elite rolling beetle's dung ball to pilfer
                const targetIdx = Math.floor(Math.random() * quarter);
                candidate = this.orderCrossover(candidate, population[targetIdx]);

                const candCost = this.computeTourCost(candidate);
                if (candCost < this.computeTourCost(population[i])) {
                    population[i] = candidate;
                }
            }

            // Update global best
            for (const t of population) {
                const c = this.computeTourCost(t);
                if (c < bestCost) {
                    bestCost = c;
                    bestTour = t;
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
