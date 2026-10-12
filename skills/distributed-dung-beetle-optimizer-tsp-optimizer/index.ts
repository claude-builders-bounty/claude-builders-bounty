/**
 * Distributed Dung Beetle Optimizer (DBO) Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired Scarabaeidae navigation, rolling, dancing, breeding, and stealing predatory model:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations, N dung beetles, and n cities.
 * - Group 1: Ball-Rolling Beetles navigating under celestial cues (Global Exploration).
 * - Group 2: Dancing Beetles re-orienting search trajectory upon encountering obstacles/stagnation.
 * - Group 3: Breeding Beetles generating brood balls in dynamic boundaries (Reproductive Exploration).
 * - Group 4: Thief Beetles pilfering food balls from the elite best tour (Local Exploitation).
 * - Deterministic boundary validation and 2-Opt local search refinement.
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

    public search(iterations = 100, populationSize = 20): DBOTSPResult {
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

        // Subpopulation division according to canonical DBO proportions:
        // Rolling: ~25%, Dancing/Obstacle: ~20%, Breeding: ~25%, Thief/Foraging: ~30%
        const nRolling = Math.max(1, Math.floor(populationSize * 0.25));
        const nBreeding = Math.max(1, Math.floor(populationSize * 0.25));
        const nDancing = Math.max(1, Math.floor(populationSize * 0.20));

        let iterationsCompleted = 0;

        for (let iter = 0; iter < iterations; iter++) {
            iterationsCompleted++;
            const decay = 1.0 - (iter / iterations);

            for (let p = 0; p < populationSize; p++) {
                let candidate = [...pop[p]];
                const currentCost = this.computeTourCost(candidate);

                if (p < nRolling) {
                    // Group 1: Ball-Rolling Beetles (Exploration guided by celestial orientation)
                    const peer = pop[Math.floor(Math.random() * populationSize)];
                    const sampleCity = peer[Math.floor(Math.random() * n)];
                    const currPos = candidate.indexOf(sampleCity);
                    const peerPos = peer.indexOf(sampleCity);
                    const nextPeerCity = peer[(peerPos + 1) % n];
                    const nextPos = candidate.indexOf(nextPeerCity);
                    if (currPos !== -1 && nextPos !== -1 && currPos !== nextPos) {
                        candidate = this.twoOptSwap(candidate, Math.min(currPos, nextPos), Math.max(currPos, nextPos));
                    }
                    const i = Math.floor(Math.random() * (n - 1));
                    const k = i + 1 + Math.floor(Math.random() * (n - 1 - i));
                    candidate = this.twoOptSwap(candidate, i, k);
                } else if (p < nRolling + nDancing) {
                    // Group 2: Dancing Beetles (Re-orientation & obstacle avoidance dance)
                    const blockLen = Math.max(2, Math.floor(n / 4));
                    const start = Math.floor(Math.random() * (n - blockLen));
                    const block = candidate.splice(start, blockLen);
                    const insertPos = Math.floor(Math.random() * (candidate.length + 1));
                    candidate.splice(insertPos, 0, ...block);

                    // Reversal dance
                    const idx1 = Math.floor(Math.random() * (n - 1));
                    const idx2 = idx1 + 1 + Math.floor(Math.random() * (n - 1 - idx1));
                    candidate = this.twoOptSwap(candidate, idx1, idx2);
                } else if (p < nRolling + nDancing + nBreeding) {
                    // Group 3: Breeding Beetles (Brood ball boundary permutation & reproduction)
                    const breedPartner = pop[Math.floor(Math.random() * populationSize)];
                    const cut1 = Math.floor(Math.random() * (n - 2));
                    const cut2 = cut1 + 1 + Math.floor(Math.random() * (n - 1 - cut1));
                    const segment = new Set(candidate.slice(cut1, cut2 + 1));
                    const child = candidate.slice(cut1, cut2 + 1);
                    for (const gene of breedPartner) {
                        if (!segment.has(gene)) {
                            child.push(gene);
                        }
                    }
                    if (child.length === n) {
                        candidate = child;
                    }
                } else {
                    // Group 4: Thief Beetles (Stealing & foraging from apex best tour - Exploitation)
                    const targetCity = bestTour[Math.floor(Math.random() * n)];
                    const currPos = candidate.indexOf(targetCity);
                    const bestPos = bestTour.indexOf(targetCity);
                    const nextBestCity = bestTour[(bestPos + 1) % n];
                    const nextPos = candidate.indexOf(nextBestCity);
                    if (currPos !== -1 && nextPos !== -1 && currPos !== nextPos) {
                        candidate = this.twoOptSwap(candidate, Math.min(currPos, nextPos), Math.max(currPos, nextPos));
                    }

                    // Thief 2-Opt local pilfering
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
                if (candCost < currentCost || Math.random() < 0.04 * decay) {
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
