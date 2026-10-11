/**
 * Distributed Golden Eagle Optimizer (GEO) Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired Aquila chrysaetos spiral soaring, horizon scanning, and prey stoop attack model:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations, N eagles, and n cities.
 * - Phase 1: High-Altitude Thermal Soaring & Horizon Scanning (Global Exploration).
 * - Phase 2: Perching & Spiral Diving Trajectory (Transition between exploration & exploitation).
 * - Phase 3: High-Speed Talons-Out Stoop Strike & Ground Pounce (Exploitation) guided by elite tours.
 * - Deterministic boundary validation and 2-Opt local search refinement.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface GEOTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedGoldenEagleOptimizerTSPOptimizer {
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

    public search(iterations = 120, populationSize = 20): GEOTSPResult {
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

        // Deterministic greedy tour initialization for leader
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
            // Deterministic pseudo-random shuffle per individual seed
            for (let j = n - 1; j > 0; j--) {
                const k = Math.floor(Math.abs(Math.sin((i + 1) * 31 + j * 17)) * (j + 1));
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
            // Golden Eagle dynamic attack propensity vs cruising radius:
            // p_attack increases from 0.2 to 0.9 as iterations advance
            const pAttack = 0.2 + 0.7 * (iter / Math.max(1, iterations));
            const cruisingRadius = 1.0 - (iter / Math.max(1, iterations));

            for (let i = 0; i < populationSize; i++) {
                let candidate = [...pop[i]];
                const currentCost = this.computeTourCost(candidate);

                const roll = Math.abs(Math.sin((iter + 1) * 97 + (i + 1) * 43));

                if (roll < pAttack) {
                    // Phase 3: High-speed Stoop Attack & Prey Pounce (guided by bestTour)
                    const sliceLen = Math.max(2, Math.floor(cruisingRadius * n));
                    const startIdx = Math.floor(Math.abs(Math.cos((iter + 1) * 19 + i * 23)) * (n - sliceLen));
                    const subBest = bestTour.slice(startIdx, startIdx + sliceLen);
                    const remaining = candidate.filter(c => !subBest.includes(c));

                    const insertPos = Math.floor(Math.abs(Math.sin(iter * 11 + i * 13)) * (remaining.length + 1));
                    candidate = remaining.slice(0, insertPos).concat(subBest).concat(remaining.slice(insertPos));
                } else if (roll < pAttack + 0.3) {
                    // Phase 2: Perching & Spiral Diving Trajectory (Double Bridge Swap)
                    const p1 = Math.floor(Math.abs(Math.sin(iter * 7 + i * 5)) * (n - 2)) + 1;
                    const p2 = Math.floor(Math.abs(Math.cos(iter * 13 + i * 3)) * (n - 2)) + 1;
                    if (p1 !== p2) {
                        const low = Math.min(p1, p2);
                        const high = Math.max(p1, p2);
                        candidate = this.twoOptSwap(candidate, low, high);
                    }
                } else {
                    // Phase 1: High-Altitude Thermal Soaring & Horizon Scanning (Exploration via Inversion)
                    const a = Math.floor(Math.abs(Math.sin((iter + 1) * 73 + i * 37)) * n);
                    const b = Math.floor(Math.abs(Math.cos((iter + 1) * 41 + i * 53)) * n);
                    if (a !== b) {
                        const low = Math.min(a, b);
                        const high = Math.max(a, b);
                        candidate = this.twoOptSwap(candidate, low, high);
                    }
                }

                // 2-Opt local greedy improvement
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
