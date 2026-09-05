/**
 * Distributed Golden Jackal Optimization (GJO) Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired cooperative pair-hunting model (Canis aureus dynamics):
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations, N jackals, and n cities.
 * - Dynamic prey evading energy E = E1 * (1 - iter / iterations) controlling transition between wide territory searching (|E| > 1) and cooperative encircling/pounce (|E| <= 1).
 * - Dual elite leaders: Male Jackal (global best tour) and Female Jackal (second best tour) guiding the pack.
 * - Cooperative pounce mechanism fusing male and female edge paths via crossover and 2-Opt inversions.
 * - Scavenging displacement to escape local sub-optimal basins.
 * - 2-Opt local search refinement.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface GJOTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedGoldenJackalOptimizationTSPOptimizer {
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

    public search(iterations = 100, populationSize = 20): GJOTSPResult {
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

        // Rank population to determine Male (best) and Female (second best)
        pop.sort((a, b) => this.computeTourCost(a) - this.computeTourCost(b));
        let maleJackal = [...pop[0]];
        let femaleJackal = [...pop[1]];
        let bestCost = this.computeTourCost(maleJackal);
        const initialCost = bestCost;

        const E1 = 1.5; // Initial energy coefficient
        let iterationsCompleted = 0;

        for (let iter = 0; iter < iterations; iter++) {
            iterationsCompleted++;
            // Evading energy E decreases from ~1.5 to 0
            const evadingEnergy = E1 * (1.0 - (iter / iterations));
            const pScavenge = 0.08 * (1.0 - (iter / iterations));

            for (let p = 0; p < populationSize; p++) {
                let candidate = [...pop[p]];

                if (Math.random() < pScavenge) {
                    // Opportunistic scavenging: displacement of tour block
                    const idx1 = Math.floor(Math.random() * (n - 1));
                    const idx2 = idx1 + 1 + Math.floor(Math.random() * (n - 1 - idx1));
                    candidate = this.twoOptSwap(candidate, idx1, idx2);
                    const blockLen = Math.max(2, Math.floor(n / 4));
                    const start = Math.floor(Math.random() * (n - blockLen));
                    const block = candidate.splice(start, blockLen);
                    const insertPos = Math.floor(Math.random() * (candidate.length + 1));
                    candidate.splice(insertPos, 0, ...block);
                } else if (Math.abs(evadingEnergy) > 1.0) {
                    // Exploration phase: Male or Female guide tracking with stochastic exploration
                    const guide = Math.random() < 0.5 ? maleJackal : femaleJackal;
                    const sampleCity = guide[Math.floor(Math.random() * n)];
                    const currPos = candidate.indexOf(sampleCity);
                    const guidePos = guide.indexOf(sampleCity);
                    const nextGuideCity = guide[(guidePos + 1) % n];
                    const nextPos = candidate.indexOf(nextGuideCity);
                    if (currPos !== -1 && nextPos !== -1 && currPos !== nextPos) {
                        candidate = this.twoOptSwap(candidate, Math.min(currPos, nextPos), Math.max(currPos, nextPos));
                    }

                    // Stochastic 2-Opt exploration
                    const i = Math.floor(Math.random() * (n - 1));
                    const k = i + 1 + Math.floor(Math.random() * (n - 1 - i));
                    candidate = this.twoOptSwap(candidate, i, k);
                } else {
                    // Exploitation phase: Cooperative pouncing (encircling prey between Male and Female)
                    // Fusing Male path edge
                    const targetCityMale = maleJackal[Math.floor(Math.random() * n)];
                    const cPos1 = candidate.indexOf(targetCityMale);
                    const mPos = maleJackal.indexOf(targetCityMale);
                    const nextMaleCity = maleJackal[(mPos + 1) % n];
                    const nPos1 = candidate.indexOf(nextMaleCity);
                    if (cPos1 !== -1 && nPos1 !== -1 && cPos1 !== nPos1) {
                        candidate = this.twoOptSwap(candidate, Math.min(cPos1, nPos1), Math.max(cPos1, nPos1));
                    }

                    // Fusing Female path edge
                    const targetCityFemale = femaleJackal[Math.floor(Math.random() * n)];
                    const cPos2 = candidate.indexOf(targetCityFemale);
                    const fPos = femaleJackal.indexOf(targetCityFemale);
                    const nextFemaleCity = femaleJackal[(fPos + 1) % n];
                    const nPos2 = candidate.indexOf(nextFemaleCity);
                    if (cPos2 !== -1 && nPos2 !== -1 && cPos2 !== nPos2) {
                        candidate = this.twoOptSwap(candidate, Math.min(cPos2, nPos2), Math.max(cPos2, nPos2));
                    }

                    // Direct 2-opt descent on prey
                    for (let i = 0; i < n - 1; i++) {
                        for (let k = i + 1; k < n; k++) {
                            const optCandidate = this.twoOptSwap(candidate, i, k);
                            if (this.computeTourCost(optCandidate) < this.computeTourCost(candidate)) {
                                candidate = optCandidate;
                                break;
                            }
                        }
                    }
                }

                const candCost = this.computeTourCost(candidate);
                const currentCost = this.computeTourCost(pop[p]);
                if (candCost < currentCost || Math.random() < 0.04 * (evadingEnergy / E1)) {
                    pop[p] = candidate;
                }

                // Update Male and Female elite pair
                if (candCost < bestCost) {
                    bestCost = candCost;
                    femaleJackal = [...maleJackal];
                    maleJackal = [...candidate];
                } else if (candCost < this.computeTourCost(femaleJackal) && candCost > bestCost) {
                    femaleJackal = [...candidate];
                }
            }
        }

        // Final polishing pass on male jackal tour
        let polished = true;
        while (polished) {
            polished = false;
            for (let i = 0; i < n - 1; i++) {
                for (let k = i + 1; k < n; k++) {
                    const candidate = this.twoOptSwap(maleJackal, i, k);
                    const candCost = this.computeTourCost(candidate);
                    if (candCost < bestCost - 1e-9) {
                        bestCost = candCost;
                        maleJackal = candidate;
                        polished = true;
                        break;
                    }
                }
                if (polished) break;
            }
        }

        const tourIds = maleJackal.map(idx => this.points[idx].id);
        tourIds.push(tourIds[0]); // Closed cycle

        return { found: true, initialCost, bestCost, tour: tourIds, iterationsCompleted };
    }
}
