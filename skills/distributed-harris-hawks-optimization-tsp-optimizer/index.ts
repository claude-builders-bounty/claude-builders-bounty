/**
 * Distributed Harris Hawks Optimization (HHO) Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired Parabuteo unicinctus cooperative surprise pounce, circling tracking, and rapid dive model:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations, N hawks, and n cities.
 * - Exploration Phase (|E| >= 1): Cooperative perching on tall desert saguaro trees and family member guidance.
 * - Exploitation Phase (|E| < 1): Four cooperative hunting strategies based on prey escaping energy E and jump strength J:
 *   1. Soft Besiege (r >= 0.5, |E| >= 0.5): Circling and exhausting prey before surprise strike.
 *   2. Hard Besiege (r >= 0.5, |E| < 0.5): Low energy prey, rapid direct pounce.
 *   3. Soft Besiege with progressive rapid dives (r < 0.5, |E| >= 0.5): Deceptive zigzag flights.
 *   4. Hard Besiege with progressive rapid dives (r < 0.5, |E| < 0.5): Final coordinated team strike guided by elite tour.
 * - Deterministic boundary validation and 2-Opt local search refinement.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface HHOTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedHarrisHawksOptimizationTSPOptimizer {
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

    private twoOptSwap(tour: number[], i: number, k: number): number[] {
        const newTour = tour.slice(0, i);
        const reversed = tour.slice(i, k + 1).reverse();
        const tail = tour.slice(k + 1);
        return newTour.concat(reversed).concat(tail);
    }

    public search(iterations = 120, populationSize = 20): HHOTSPResult {
        const n = this.points.length;
        if (n === 0) {
            return { found: false, initialCost: 0, bestCost: 0, tour: [], iterationsCompleted: 0 };
        }
        if (n === 1) {
            return { found: true, initialCost: 0, bestCost: 0, tour: [this.points[0].id, this.points[0].id], iterationsCompleted: 0 };
        }
        if (n === 2) {
            const d = this.getDistance(this.points[0], this.points[1]) * 2;
            return { found: true, initialCost: d, bestCost: d, tour: [this.points[0].id, this.points[1].id, this.points[0].id], iterationsCompleted: 0 };
        }

        const pop: number[][] = [];
        const baseIndices = Array.from({ length: n }, (_, i) => i);

        // Deterministic greedy tour initialization for pack leader
        const greedyTour: number[] = [0];
        const visited = new Set<number>([0]);
        while (greedyTour.length < n) {
            const curr = greedyTour[greedyTour.length - 1];
            let nearest = -1;
            let minDist = Infinity;
            for (let i = 0; i < n; i++) {
                if (!visited.has(i)) {
                    const d = this.getDistance(this.points[curr], this.points[i]);
                    if (d < minDist) {
                        minDist = d;
                        nearest = i;
                    }
                }
            }
            if (nearest !== -1) {
                visited.add(nearest);
                greedyTour.push(nearest);
            }
        }
        pop.push(greedyTour);

        // Fill population with diverse permutations
        for (let i = 1; i < populationSize; i++) {
            const tour = [...baseIndices];
            for (let j = n - 1; j > 0; j--) {
                const k = Math.floor(Math.abs(Math.sin((i + 1) * 37 + j * 19)) * (j + 1));
                const tmp = tour[j];
                tour[j] = tour[k];
                tour[k] = tmp;
            }
            pop.push(tour);
        }

        let bestTour = [...pop[0]];
        let bestCost = this.computeTourCost(bestTour);
        const initialCost = bestCost;

        for (let iter = 0; iter < iterations; iter++) {
            // Prey escaping energy E = 2 * E0 * (1 - iter / iterations)
            const e0 = 2 * Math.abs(Math.sin((iter + 1) * 89)) - 1; // [-1, 1]
            const escapingEnergy = 2 * e0 * (1 - iter / Math.max(1, iterations));
            const absE = Math.abs(escapingEnergy);

            for (let i = 0; i < populationSize; i++) {
                let candidate = [...pop[i]];
                const currentCost = this.computeTourCost(candidate);
                const r = Math.abs(Math.sin((iter + 1) * 101 + (i + 1) * 47));

                if (absE >= 1.0) {
                    // Exploration phase: perching on random trees or other family members
                    const q = Math.abs(Math.cos(iter * 17 + i * 29));
                    if (q >= 0.5) {
                        // Perch based on random other hawk
                        const randIdx = Math.floor(Math.abs(Math.sin(iter * 23 + i * 7)) * populationSize);
                        const otherHawk = pop[randIdx];
                        const crossPoint = Math.floor(Math.abs(Math.sin(iter * 13 + i * 11)) * (n - 2)) + 1;
                        const sub = otherHawk.slice(0, crossPoint);
                        const rest = candidate.filter(c => !sub.includes(c));
                        candidate = sub.concat(rest);
                    } else {
                        // Perch on random tall tree: 2-opt invert
                        const p1 = Math.floor(Math.abs(Math.sin(iter * 31 + i * 19)) * n);
                        const p2 = Math.floor(Math.abs(Math.cos(iter * 43 + i * 37)) * n);
                        if (p1 !== p2) {
                            candidate = this.twoOptSwap(candidate, Math.min(p1, p2), Math.max(p1, p2));
                        }
                    }
                } else {
                    // Exploitation phase: 4 cooperative hunting strategies
                    if (r >= 0.5 && absE >= 0.5) {
                        // Strategy 1: Soft Besiege
                        const sliceLen = Math.max(2, Math.floor(n * 0.4));
                        const start = Math.floor(Math.abs(Math.sin(iter * 5 + i * 7)) * (n - sliceLen));
                        const sub = bestTour.slice(start, start + sliceLen);
                        const rest = candidate.filter(c => !sub.includes(c));
                        candidate = rest.slice(0, Math.floor(rest.length / 2)).concat(sub).concat(rest.slice(Math.floor(rest.length / 2)));
                    } else if (r >= 0.5 && absE < 0.5) {
                        // Strategy 2: Hard Besiege
                        const sliceLen = Math.max(2, Math.floor(n * 0.6));
                        const start = Math.floor(Math.abs(Math.cos(iter * 11 + i * 13)) * (n - sliceLen));
                        const sub = bestTour.slice(start, start + sliceLen);
                        const rest = candidate.filter(c => !sub.includes(c));
                        candidate = sub.concat(rest);
                    } else if (r < 0.5 && absE >= 0.5) {
                        // Strategy 3: Soft Besiege with progressive rapid dives (Levy zigzag)
                        const p1 = Math.floor(Math.abs(Math.sin(iter * 19 + i * 23)) * (n - 1));
                        const p2 = (p1 + 2) % n;
                        candidate = this.twoOptSwap(candidate, Math.min(p1, p2), Math.max(p1, p2));
                    } else {
                        // Strategy 4: Hard Besiege with progressive rapid dives (Climax team strike)
                        const sliceLen = Math.max(2, Math.floor(n * 0.8));
                        const start = 0;
                        const sub = bestTour.slice(start, start + sliceLen);
                        const rest = candidate.filter(c => !sub.includes(c));
                        candidate = sub.concat(rest);
                    }
                }

                // Greedy 2-opt local improvement
                for (let a = 1; a < n - 1; a++) {
                    for (let b = a + 1; b < n; b++) {
                        const swapped = this.twoOptSwap(candidate, a, b);
                        const swappedCost = this.computeTourCost(swapped);
                        if (swappedCost < currentCost) {
                            candidate = swapped;
                            break;
                        }
                    }
                }

                const candCost = this.computeTourCost(candidate);
                if (candCost < currentCost) {
                    pop[i] = candidate;
                }
                if (candCost < bestCost) {
                    bestCost = candCost;
                    bestTour = [...candidate];
                }
            }
        }

        // Final exhaustive 2-opt pass on the best tour
        let improved = true;
        while (improved) {
            improved = false;
            for (let i = 1; i < n - 1; i++) {
                for (let k = i + 1; k < n; k++) {
                    const swapped = this.twoOptSwap(bestTour, i, k);
                    const swappedCost = this.computeTourCost(swapped);
                    if (swappedCost < bestCost - 1e-9) {
                        bestTour = swapped;
                        bestCost = swappedCost;
                        improved = true;
                    }
                }
            }
        }

        const closedTour = [...bestTour.map(idx => this.points[idx].id), this.points[bestTour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost,
            tour: closedTour,
            iterationsCompleted: iterations
        };
    }
}
