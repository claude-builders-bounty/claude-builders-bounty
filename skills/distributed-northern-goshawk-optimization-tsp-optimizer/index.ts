/**
 * Distributed Northern Goshawk Optimization (NGO) Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired Accipiter gentilis predatory pursuit and tail-chase dive dynamics:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations, N goshawks, and n cities.
 * - Phase 1: Prey Identification & Open Pursuit (Exploration): Goshawk selects random prey from the flock or tracks the global elite target, combining paths via Order Crossover (OX).
 * - Phase 2: Tail-Chase & Evasive Dive (Exploitation): Close-range pursuit modeling prey evasive zigzags and goshawk rapid dives with localized subtour reversals within a shrinking radius.
 * - Memory matrix greedy replacement and 2-Opt local search refinement.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface NGOTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedNorthernGoshawkOptimizationTSPOptimizer {
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

    private tailChaseDive(tour: number[], prng: () => number, radius: number): number[] {
        const n = tour.length;
        if (n < 4) return [...tour];
        const copy = [...tour];
        const maxSpan = Math.max(2, Math.floor(n * radius));
        const i = Math.floor(prng() * (n - 2));
        const span = 2 + Math.floor(prng() * Math.min(maxSpan, n - i - 1));
        const j = i + span;
        const sub = copy.slice(i, j + 1).reverse();
        copy.splice(i, sub.length, ...sub);
        return copy;
    }

    public search(maxIterations = 120, populationSize = 25, seed = 92): NGOTSPResult {
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

        // Randomly initialized goshawks
        const baseIndices = Array.from({ length: n }, (_, i) => i);
        for (let i = 1; i < popSize; i++) {
            const shuffled = [...baseIndices];
            for (let j = n - 1; j > 0; j--) {
                const k = Math.floor(prng() * (j + 1));
                [shuffled[j], shuffled[k]] = [shuffled[k], shuffled[j]];
            }
            population.push(shuffled);
        }

        // Identify initial best goshawk
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

        // NGO Optimization Loop
        for (let iter = 0; iter < maxIterations; iter++) {
            const radius = 0.02 * (1 - iter / maxIterations) + 0.1;

            for (let i = 0; i < popSize; i++) {
                // Phase 1: Prey identification & pursuit
                const targetIdx = Math.floor(prng() * popSize);
                const targetTour = prng() < 0.6 ? bestTour : population[targetIdx];
                const cut1 = Math.floor(prng() * n);
                const cut2 = Math.floor(prng() * n);
                let p1Candidate = this.orderCrossover(targetTour, population[i], cut1, cut2);
                let p1Cost = this.computeTourCost(p1Candidate);

                if (p1Cost < this.computeTourCost(population[i])) {
                    population[i] = p1Candidate;
                    if (p1Cost < bestCost) {
                        bestCost = p1Cost;
                        bestTour = [...p1Candidate];
                    }
                }

                // Phase 2: Tail-chase & evasive dive
                let p2Candidate = this.tailChaseDive(population[i], prng, radius);
                let p2Cost = this.computeTourCost(p2Candidate);

                if (p2Cost < this.computeTourCost(population[i])) {
                    population[i] = p2Candidate;
                    if (p2Cost < bestCost) {
                        bestCost = p2Cost;
                        bestTour = [...p2Candidate];
                    }
                }
            }
        }

        // 2-Opt local search refinement on the final best goshawk tour
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
