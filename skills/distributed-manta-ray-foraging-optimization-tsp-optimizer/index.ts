/**
 * Distributed Manta Ray Foraging Optimization (MRFO) Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired marine megafauna filter-feeding model (Mobula birostris dynamics):
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations, N manta rays, and n cities.
 * - Phase 1: Chain foraging (Exploration). Rays align head-to-tail, following the best plankton cache and the predecessor in the chain.
 * - Phase 2: Cyclone foraging (Exploitation). Spiral vortex aggregation tightening around the optimal route.
 * - Phase 3: Somersault foraging (Escaping local basins). Backward acrobatic loop around a pivot vertex inverting route subsegments.
 * - 2-Opt local search refinement and deterministic boundary validation.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface MRFOTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedMantaRayForagingOptimizationTSPOptimizer {
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

    public search(iterations = 100, populationSize = 20): MRFOTSPResult {
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

        for (let p = 0; p < populationSize; p++) {
            const ind = [...baseIndices];
            for (let i = ind.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [ind[i], ind[j]] = [ind[j], ind[i]];
            }
            pop.push(ind);
        }

        let bestTour = [...pop[0]];
        let bestCost = this.computeTourCost(bestTour);
        const initialCost = bestCost;

        for (let p = 1; p < populationSize; p++) {
            const c = this.computeTourCost(pop[p]);
            if (c < bestCost) {
                bestCost = c;
                bestTour = [...pop[p]];
            }
        }

        let iterationsCompleted = 0;

        for (let iter = 0; iter < iterations; iter++) {
            iterationsCompleted++;
            const progress = iter / iterations;

            for (let p = 0; p < populationSize; p++) {
                let candidate = [...pop[p]];
                const currentCost = this.computeTourCost(candidate);

                const strategyRoll = Math.random();

                if (strategyRoll < 0.45) {
                    // Phase 1: Chain Foraging
                    // Align with best plankton position and chain predecessor
                    const predecessor = p === 0 ? bestTour : pop[p - 1];
                    const sampleCity = predecessor[Math.floor(Math.random() * n)];
                    const currPos = candidate.indexOf(sampleCity);
                    const predPos = predecessor.indexOf(sampleCity);
                    const nextPredCity = predecessor[(predPos + 1) % n];
                    const nextPos = candidate.indexOf(nextPredCity);
                    if (currPos !== -1 && nextPos !== -1 && currPos !== nextPos) {
                        candidate = this.twoOptSwap(candidate, Math.min(currPos, nextPos), Math.max(currPos, nextPos));
                    }

                    // Guidance from global best plankton patch
                    if (Math.random() < 0.5) {
                        const targetCity = bestTour[Math.floor(Math.random() * n)];
                        const cPos = candidate.indexOf(targetCity);
                        const bPos = bestTour.indexOf(targetCity);
                        const nextBestCity = bestTour[(bPos + 1) % n];
                        const nPos = candidate.indexOf(nextBestCity);
                        if (cPos !== -1 && nPos !== -1 && cPos !== nPos) {
                            candidate = this.twoOptSwap(candidate, Math.min(cPos, nPos), Math.max(cPos, nPos));
                        }
                    }
                } else if (strategyRoll < 0.8) {
                    // Phase 2: Cyclone Foraging
                    // Spiral vortex converging onto best tour
                    const targetCity = bestTour[Math.floor(Math.random() * n)];
                    const cPos = candidate.indexOf(targetCity);
                    const bPos = bestTour.indexOf(targetCity);
                    const nextBestCity = bestTour[(bPos + 1) % n];
                    const nPos = candidate.indexOf(nextBestCity);
                    if (cPos !== -1 && nPos !== -1 && cPos !== nPos) {
                        candidate = this.twoOptSwap(candidate, Math.min(cPos, nPos), Math.max(cPos, nPos));
                    }

                    // Direct 2-opt descent on cyclone eye
                    for (let i = 0; i < n - 1; i++) {
                        for (let k = i + 1; k < n; k++) {
                            const optCandidate = this.twoOptSwap(candidate, i, k);
                            if (this.computeTourCost(optCandidate) < this.computeTourCost(candidate)) {
                                candidate = optCandidate;
                                break;
                            }
                        }
                    }
                } else {
                    // Phase 3: Somersault Foraging
                    // Backward loop around food pivot: somersault inversion of tour block
                    const pivot = Math.floor(Math.random() * n);
                    const halfSpan = Math.max(2, Math.floor(n / 3));
                    const start = (pivot - Math.floor(halfSpan / 2) + n) % n;
                    const end = (start + halfSpan) % n;
                    if (start < end) {
                        candidate = this.twoOptSwap(candidate, start, end);
                    } else {
                        const i = Math.floor(Math.random() * (n - 1));
                        const k = i + 1 + Math.floor(Math.random() * (n - 1 - i));
                        candidate = this.twoOptSwap(candidate, i, k);
                    }
                }

                const candCost = this.computeTourCost(candidate);
                if (candCost < currentCost || Math.random() < 0.04 * (1.0 - progress)) {
                    pop[p] = candidate;
                }
                if (candCost < bestCost) {
                    bestCost = candCost;
                    bestTour = [...candidate];
                }
            }
        }

        // Final polishing pass on best tour
        let polished = true;
        while (polished) {
            polished = false;
            for (let i = 0; i < n - 1; i++) {
                for (let k = i + 1; k < n; k++) {
                    const candidate = this.twoOptSwap(bestTour, i, k);
                    const candCost = this.computeTourCost(candidate);
                    if (candCost < bestCost - 1e-9) {
                        bestCost = candCost;
                        bestTour = candidate;
                        polished = true;
                        break;
                    }
                }
                if (polished) break;
            }
        }

        const tourIds = bestTour.map(idx => this.points[idx].id);
        tourIds.push(tourIds[0]); // Closed cycle

        return { found: true, initialCost, bestCost, tour: tourIds, iterationsCompleted };
    }
}
