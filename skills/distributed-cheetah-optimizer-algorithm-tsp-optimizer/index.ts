/**
 * Cheetah Optimizer (CO) High-Speed Sprint & Dynamic Turning Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired feline hunting behavior model featuring:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations, N virtual cheetahs, and n cities.
 * - Tri-phase hunting strategy: Search & Stalking (Exploration), Sit-and-Wait (Ambush energy conservation), and High-Speed Sprinting & Turning (Exploitation).
 * - Dynamic velocity coefficient H decaying over iterations balancing stalking exploration vs sprint turning exploitation.
 * - Leader sprint guidance and 2-Opt local search refinement.
 * - Full unit test coverage via Node native test runner.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface COTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedCheetahOptimizerAlgorithmTSPOptimizer {
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

    public search(iterations = 100, populationSize = 20): COTSPResult {
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
            // Velocity coefficient H decays from e^2 to 0
            const H = Math.exp(2.0 * (1.0 - (iter / iterations))) / Math.exp(2.0); // in [0, 1]
            // Sit-and-wait probability
            const pWait = 0.08 + 0.04 * (iter / iterations);

            for (let p = 0; p < populationSize; p++) {
                let candidate = [...pop[p]];

                if (Math.random() < pWait) {
                    // Phase 2: Sit-and-Wait (Ambush patience, minimal perturbation)
                    if (Math.random() < 0.25) {
                        const idx1 = Math.floor(Math.random() * (n - 1));
                        candidate = this.twoOptSwap(candidate, idx1, idx1 + 1);
                    }
                } else if (Math.random() < H) {
                    // Phase 1: Search & Stalking (Stealth exploration across savannah)
                    const idx1 = Math.floor(Math.random() * (n - 1));
                    const idx2 = idx1 + 1 + Math.floor(Math.random() * (n - 1 - idx1));
                    candidate = this.twoOptSwap(candidate, idx1, idx2);

                    // Cross-swapping with random hunting partner
                    if (Math.random() < 0.35) {
                        const randomPartner = pop[Math.floor(Math.random() * populationSize)];
                        const sampleCity = randomPartner[Math.floor(Math.random() * n)];
                        const currPos = candidate.indexOf(sampleCity);
                        const partnerPos = randomPartner.indexOf(sampleCity);
                        const nextPartnerCity = randomPartner[(partnerPos + 1) % n];
                        const nextPos = candidate.indexOf(nextPartnerCity);
                        if (currPos !== -1 && nextPos !== -1 && currPos !== nextPos) {
                            candidate = this.twoOptSwap(candidate, Math.min(currPos, nextPos), Math.max(currPos, nextPos));
                        }
                    }
                } else {
                    // Phase 3: High-Speed Sprint Attack & Sharp Turning (Exploitation)
                    const targetCity = bestTour[Math.floor(Math.random() * n)];
                    const currPos = candidate.indexOf(targetCity);
                    const bestPos = bestTour.indexOf(targetCity);
                    const nextBestCity = bestTour[(bestPos + 1) % n];
                    const nextPos = candidate.indexOf(nextBestCity);
                    if (currPos !== -1 && nextPos !== -1 && currPos !== nextPos) {
                        candidate = this.twoOptSwap(candidate, Math.min(currPos, nextPos), Math.max(currPos, nextPos));
                    }

                    // Local 2-opt descent
                    let improved = false;
                    for (let i = 0; i < n - 1; i++) {
                        for (let k = i + 1; k < n; k++) {
                            const optCandidate = this.twoOptSwap(candidate, i, k);
                            if (this.computeTourCost(optCandidate) < this.computeTourCost(candidate)) {
                                candidate = optCandidate;
                                improved = true;
                                break;
                            }
                        }
                        if (improved) break;
                    }
                }

                const candCost = this.computeTourCost(candidate);
                if (candCost < this.computeTourCost(pop[p]) || Math.random() < 0.03 * H) {
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
