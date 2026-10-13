/**
 * Distributed Coati Optimization Algorithm (COA) Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired cooperative hunting and predator evasion behavior of Nasua nasua (coati):
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations, N coatis, and n cities.
 * - Two Behavioral Phases:
 *   1. Canopy Iguana Hunting (Exploration): Half the coatis climb trees to shake branches while the other half wait on the ground (Order Crossover towards prey/canopy leader).
 *   2. Ground Ambush & Predator Evasion (Exploitation): Rapid localized zig-zag sweeps around fallen prey avoiding predators (localized subsegment inversions & city swaps).
 * - 2-Opt local search refinement for post-hunt tour convergence.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface COAResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedCoatiOptimizationAlgorithmTSPOptimizer {
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
     * Discrete Order Crossover (OX) simulating coatis climbing towards iguana canopy position.
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
     * Ground ambush subsegment reversal: Simulates rapid ground intercept.
     */
    private groundAmbushInversion(tour: string[]): string[] {
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
     * Zig-zag evasion swap: Simulates predator evasion dodge.
     */
    private zigZagEvasionSwap(tour: string[]): string[] {
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
     * 2-Opt local search refinement for post-hunt tour convergence.
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

    public search(maxIterations = 100, coatiCount = 25): COAResult {
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

        const size = Math.max(8, coatiCount);
        const population: string[][] = [];
        for (let i = 0; i < size; i++) {
            population.push(this.createRandomTour());
        }

        let bestIguanaTour = population[0]; // Global best tour position (iguana)
        let bestIguanaCost = this.computeTourCost(bestIguanaTour);

        for (const t of population) {
            const c = this.computeTourCost(t);
            if (c < bestIguanaCost) {
                bestIguanaCost = c;
                bestIguanaTour = t;
            }
        }

        const initialCost = bestIguanaCost;

        for (let iter = 0; iter < maxIterations; iter++) {
            const half = Math.floor(size / 2);

            for (let i = 0; i < size; i++) {
                let candidate = population[i];

                // Phase 1: Hunting Iguana in Canopy vs Ground Waiting
                if (i < half) {
                    // Tree climbers: Direct crossover towards iguana position
                    candidate = this.orderCrossover(candidate, bestIguanaTour);
                } else {
                    // Ground waiters: Random peer coordination and branch shaking response
                    const peer = population[Math.floor(Math.random() * size)];
                    candidate = this.orderCrossover(candidate, peer);
                    candidate = this.groundAmbushInversion(candidate);
                }

                let candCost = this.computeTourCost(candidate);
                let currCost = this.computeTourCost(population[i]);

                if (candCost < currCost) {
                    population[i] = candidate;
                    if (candCost < bestIguanaCost) {
                        bestIguanaCost = candCost;
                        bestIguanaTour = candidate;
                    }
                }

                // Phase 2: Escaping from Predators & Ground Snatch (Exploitation)
                let evasionCandidate = population[i];
                if (Math.random() < 0.5) {
                    evasionCandidate = this.groundAmbushInversion(evasionCandidate);
                } else {
                    evasionCandidate = this.zigZagEvasionSwap(evasionCandidate);
                }

                const evasionCost = this.computeTourCost(evasionCandidate);
                currCost = this.computeTourCost(population[i]);

                if (evasionCost < currCost) {
                    population[i] = evasionCandidate;
                    if (evasionCost < bestIguanaCost) {
                        bestIguanaCost = evasionCost;
                        bestIguanaTour = evasionCandidate;
                    }
                }
            }
        }

        // Post-hunt 2-Opt local refinement on elite tour
        const refinedTour = this.apply2Opt(bestIguanaTour);
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
