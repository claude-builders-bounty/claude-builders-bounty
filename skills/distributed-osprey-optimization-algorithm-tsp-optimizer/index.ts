/**
 * Distributed Osprey Optimization Algorithm (OOA) Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired marine hunting and talon-carry foraging behavior of Pandion haliaetus (osprey / sea hawk):
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations, N ospreys, and n cities.
 * - Two Behavioral Phases:
 *   1. Position Identification & Hunting Dive (Exploration): Ospreys soar over water, detect marine fish positions, and dive talons-first (Order Crossover towards global best marine prey/leader).
 *   2. Carrying Fish to Suitable Perch (Exploitation): Navigating with caught prey to elevated nesting roosts (localized subsegment inversions & city swaps).
 * - 2-Opt local search refinement for post-catch tour convergence.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface OOAResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedOspreyOptimizationAlgorithmTSPOptimizer {
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
     * Discrete Order Crossover (OX) simulating osprey dive talons-first towards marine fish.
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
     * Talon grip reversal: Inverts a subsegment representing carrying fish to roost.
     */
    private talonGripInversion(tour: string[]): string[] {
        const clean = tour.slice(0, tour.length - 1);
        const n = clean.length;
        if (n <= 3) return [...tour];

        const i = Math.floor(Math.random() * (n - 2)) + 1;
        const j = Math.min(n - 1, i + Math.floor(Math.random() * 3) + 1);
        const sub = clean.slice(i, j + 1).reverse();
        clean.splice(i, sub.length, ...sub);

        return [...clean, clean[0]];
    }

    /**
     * Aerial perch adjustment swap: Exchanges two cities simulating landing angle trim.
     */
    private perchAdjustmentSwap(tour: string[]): string[] {
        const clean = tour.slice(0, tour.length - 1);
        const n = clean.length;
        if (n <= 3) return [...tour];

        const i = Math.floor(Math.random() * n);
        const j = (i + 1) % n;
        const tmp = clean[i];
        clean[i] = clean[j];
        clean[j] = tmp;

        return [...clean, clean[0]];
    }

    /**
     * 2-Opt local search refinement for post-catch tour convergence.
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

    public search(maxIterations = 100, ospreyCount = 25): OOAResult {
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

        const size = Math.max(8, ospreyCount);
        const population: string[][] = [];
        for (let i = 0; i < size; i++) {
            population.push(this.createRandomTour());
        }

        let bestFishTour = population[0]; // Global best fish prey position
        let bestFishCost = this.computeTourCost(bestFishTour);

        for (const t of population) {
            const c = this.computeTourCost(t);
            if (c < bestFishCost) {
                bestFishCost = c;
                bestFishTour = t;
            }
        }

        const initialCost = bestFishCost;

        for (let iter = 0; iter < maxIterations; iter++) {
            for (let i = 0; i < size; i++) {
                let candidate = population[i];

                // Phase 1: Fish position detection & hunting dive (Exploration)
                const randChoice = Math.random();
                if (randChoice < 0.5) {
                    candidate = this.orderCrossover(candidate, bestFishTour);
                } else {
                    const peer = population[Math.floor(Math.random() * size)];
                    candidate = this.orderCrossover(candidate, peer);
                }

                let candCost = this.computeTourCost(candidate);
                let currCost = this.computeTourCost(population[i]);

                if (candCost < currCost) {
                    population[i] = candidate;
                    if (candCost < bestFishCost) {
                        bestFishCost = candCost;
                        bestFishTour = candidate;
                    }
                }

                // Phase 2: Carrying the fish to roost / perch (Exploitation)
                let perchCandidate = population[i];
                if (Math.random() < 0.5) {
                    perchCandidate = this.talonGripInversion(perchCandidate);
                } else {
                    perchCandidate = this.perchAdjustmentSwap(perchCandidate);
                }

                const perchCost = this.computeTourCost(perchCandidate);
                currCost = this.computeTourCost(population[i]);

                if (perchCost < currCost) {
                    population[i] = perchCandidate;
                    if (perchCost < bestFishCost) {
                        bestFishCost = perchCost;
                        bestFishTour = perchCandidate;
                    }
                }
            }
        }

        // Post-hunt 2-Opt local refinement on elite tour
        const refinedTour = this.apply2Opt(bestFishTour);
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
