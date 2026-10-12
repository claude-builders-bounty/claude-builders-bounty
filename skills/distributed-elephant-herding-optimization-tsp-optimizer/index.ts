/**
 * Distributed Elephant Herding Optimization (EHO) Metaheuristic for Traveling Salesperson Problem (TSP).
 * Bio-inspired Loxodonta africana matriarchal clan dynamics:
 * - O(I \cdot K \cdot M \cdot n) polynomial time complexity across I iterations, K clans, M clan members, and n cities.
 * - Clan Structure: Population divided into distinct clans, each led by an experienced matriarch (clan best tour).
 * - Clan Updating Operator: Calves and young elephants update their foraging trajectories guided by the matriarch using Order Crossover (OX) and localized mutation.
 * - Separating Operator: Male mature elephants leave the clan to explore distant savannah territories, generating novel diversified permutations.
 * - 2-Opt local search refinement applied to the global matriarch elite tour.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface EHOTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedElephantHerdingOptimizationTSPOptimizer {
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

    public search(maxIterations = 120, numClans = 3, elephantsPerClan = 8, seed = 55): EHOTSPResult {
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

        const clansCount = Math.max(2, numClans);
        const clanSize = Math.max(4, elephantsPerClan);
        const totalElephants = clansCount * clanSize;

        // Initialize clans
        const nnTour = this.buildNearestNeighborTour();
        const baseIndices = Array.from({ length: n }, (_, i) => i);
        const clans: number[][][] = [];

        let globalMatriarch = [...nnTour];
        let globalBestCost = this.computeTourCost(globalMatriarch);
        const initialCost = globalBestCost;

        for (let c = 0; c < clansCount; c++) {
            const clan: number[][] = [];
            for (let e = 0; e < clanSize; e++) {
                if (c === 0 && e === 0) {
                    clan.push([...nnTour]);
                } else {
                    const shuffled = [...baseIndices];
                    for (let j = n - 1; j > 0; j--) {
                        const k = Math.floor(prng() * (j + 1));
                        [shuffled[j], shuffled[k]] = [shuffled[k], shuffled[j]];
                    }
                    const cost = this.computeTourCost(shuffled);
                    if (cost < globalBestCost) {
                        globalBestCost = cost;
                        globalMatriarch = [...shuffled];
                    }
                    clan.push(shuffled);
                }
            }
            clans.push(clan);
        }

        // EHO Optimization Loop
        for (let iter = 0; iter < maxIterations; iter++) {
            for (let c = 0; c < clansCount; c++) {
                const clan = clans[c];

                // Identify clan matriarch (best) and worst elephant
                let matriarchIdx = 0;
                let matriarchCost = this.computeTourCost(clan[0]);
                let worstIdx = 0;
                let worstCost = matriarchCost;

                for (let e = 1; e < clanSize; e++) {
                    const cost = this.computeTourCost(clan[e]);
                    if (cost < matriarchCost) {
                        matriarchCost = cost;
                        matriarchIdx = e;
                    }
                    if (cost > worstCost) {
                        worstCost = cost;
                        worstIdx = e;
                    }
                }

                const matriarch = clan[matriarchIdx];
                if (matriarchCost < globalBestCost) {
                    globalBestCost = matriarchCost;
                    globalMatriarch = [...matriarch];
                }

                // Clan Updating Operator: Calves follow the matriarch
                for (let e = 0; e < clanSize; e++) {
                    if (e === matriarchIdx) {
                        // Matriarch performs exploratory subtle shifts
                        if (prng() < 0.4 && n >= 4) {
                            const candidate = [...matriarch];
                            const i1 = Math.floor(prng() * n);
                            const i2 = (i1 + 1) % n;
                            const tmp = candidate[i1];
                            candidate[i1] = candidate[i2];
                            candidate[i2] = tmp;
                            if (this.computeTourCost(candidate) < matriarchCost) {
                                clan[e] = candidate;
                            }
                        }
                    } else {
                        // Calf moves towards matriarch with crossover
                        const cut1 = Math.floor(prng() * n);
                        const cut2 = Math.floor(prng() * n);
                        const updated = this.orderCrossover(matriarch, clan[e], cut1, cut2);
                        if (this.computeTourCost(updated) < this.computeTourCost(clan[e])) {
                            clan[e] = updated;
                        }
                    }
                }

                // Separating Operator: Worst elephant leaves clan and explores independently
                if (prng() < 0.7) {
                    const explorer = [...baseIndices];
                    for (let j = n - 1; j > 0; j--) {
                        const k = Math.floor(prng() * (j + 1));
                        [explorer[j], explorer[k]] = [explorer[k], explorer[j]];
                    }
                    clan[worstIdx] = explorer;
                }
            }
        }

        // 2-Opt refinement on the global matriarch
        globalMatriarch = this.twoOpt(globalMatriarch);
        globalBestCost = this.computeTourCost(globalMatriarch);

        const tourIds = globalMatriarch.map(idx => this.points[idx].id);
        tourIds.push(tourIds[0]);

        return {
            found: true,
            initialCost,
            bestCost: globalBestCost,
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
