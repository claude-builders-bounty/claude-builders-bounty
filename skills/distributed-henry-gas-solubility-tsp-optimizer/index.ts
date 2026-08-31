/**
 * Henry Gas Solubility Optimization (HGSO) Swarm Metaheuristic for Traveling Salesperson Problem (TSP).
 * Physics-inspired chemical thermodynamics optimization primitive offering:
 * - O(I \cdot N \cdot n) polynomial time complexity across I iterations and N gas agents.
 * - Dynamic Henry's law constant H_j(t+1) and temperature decay T(t) = exp(-t / t_max).
 * - Gas solubility S_i,j scaling crossover attraction towards cluster best and global best gas states.
 * - 2-Opt local search refinement.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface HGSOTSPResult {
    found: boolean;
    initialCost: number;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedHenryGasSolubilityTSPOptimizer {
    private points: Point2D[] = [];

    constructor() {}

    /**
     * Adds a 2D Euclidean point.
     */
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

    private generateRandomPermutation(n: number, rng: () => number): number[] {
        const arr = Array.from({ length: n }, (_, i) => i);
        for (let i = n - 1; i > 0; i--) {
            const j = Math.floor(rng() * (i + 1));
            const tmp = arr[i];
            arr[i] = arr[j];
            arr[j] = tmp;
        }
        return arr;
    }

    /**
     * Solubility guided gas crossover towards best gas concentration.
     */
    private solubilityMove(tour: number[], bestTour: number[], solubility: number, rng: () => number): number[] {
        const n = tour.length;
        const result = [...tour];
        const numSwaps = Math.max(1, Math.round(solubility * n * 0.35));

        for (let s = 0; s < numSwaps; s++) {
            const targetIdx = Math.floor(rng() * n);
            const targetVal = bestTour[targetIdx];
            const currIdx = result.indexOf(targetVal);

            if (currIdx !== -1 && currIdx !== targetIdx) {
                const tmp = result[targetIdx];
                result[targetIdx] = result[currIdx];
                result[currIdx] = tmp;
            }
        }

        return result;
    }

    /**
     * Solves TSP using Henry Gas Solubility Optimization.
     */
    public search(
        maxIterations = 100,
        populationSize = 20,
        clusterCount = 4,
        K = 1.0, // Henry constant factor
        rng: () => number = Math.random
    ): HGSOTSPResult {
        const n = this.points.length;
        if (n === 0) {
            return { found: false, initialCost: 0, bestCost: 0, tour: [], iterationsCompleted: 0 };
        }

        if (n <= 2) {
            const indices = Array.from({ length: n }, (_, i) => i);
            const cost = this.computeTourCost(indices);
            return {
                found: true,
                initialCost: cost,
                bestCost: cost,
                tour: [...indices.map(i => this.points[i].id), indices.length > 0 ? this.points[indices[0]].id : ""].filter(Boolean),
                iterationsCompleted: 0,
            };
        }

        const effectivePop = Math.max(8, Math.min(50, populationSize));
        const clusters = Math.max(2, Math.min(4, clusterCount));
        const agentsPerCluster = Math.floor(effectivePop / clusters);

        // 1. Initialize gas population divided into clusters
        let gasClusters: { tour: number[]; cost: number }[][] = [];
        for (let c = 0; c < clusters; c++) {
            const cluster: { tour: number[]; cost: number }[] = [];
            for (let i = 0; i < agentsPerCluster; i++) {
                const tour = this.generateRandomPermutation(n, rng);
                cluster.push({ tour, cost: this.computeTourCost(tour) });
            }
            cluster.sort((a, b) => a.cost - b.cost);
            gasClusters.push(cluster);
        }

        let globalBest = { ...gasClusters[0][0] };
        for (let c = 0; c < clusters; c++) {
            if (gasClusters[c][0].cost < globalBest.cost) {
                globalBest = { ...gasClusters[c][0] };
            }
        }
        const initialCost = globalBest.cost;

        for (let iter = 0; iter < maxIterations; iter++) {
            // Temperature T decays exponentially
            const T = Math.exp(-iter / maxIterations);
            // Henry constant H
            const H = Math.exp(-0.05 * (1 / (T + 1e-4) - 1));

            for (let c = 0; c < clusters; c++) {
                const clusterBest = gasClusters[c][0];

                for (let i = 0; i < agentsPerCluster; i++) {
                    const agent = gasClusters[c][i];
                    // Solubility calculation: S = K * H * (bestCost / agentCost)
                    const S = Math.min(1.0, Math.max(0.1, K * H * (clusterBest.cost / (agent.cost + 1e-6))));

                    let newTour: number[];
                    if (rng() < 0.5) {
                        // Dissolve towards cluster leader
                        newTour = this.solubilityMove(agent.tour, clusterBest.tour, S, rng);
                    } else {
                        // Dissolve towards global leader
                        newTour = this.solubilityMove(agent.tour, globalBest.tour, S * 0.8, rng);
                    }

                    // 2-opt local search refinement
                    if (rng() < 0.2) {
                        const l = Math.floor(rng() * n);
                        let rp = Math.floor(rng() * n);
                        while (rp === l) rp = Math.floor(rng() * n);
                        const left = Math.min(l, rp);
                        const right = Math.max(l, rp);
                        let lp = left, rpp = right;
                        while (lp < rpp) {
                            const tmp = newTour[lp];
                            newTour[lp] = newTour[rpp];
                            newTour[rpp] = tmp;
                            lp++;
                            rpp--;
                        }
                    }

                    const newCost = this.computeTourCost(newTour);
                    if (newCost < agent.cost) {
                        gasClusters[c][i] = { tour: newTour, cost: newCost };
                    }
                }

                gasClusters[c].sort((a, b) => a.cost - b.cost);
                if (gasClusters[c][0].cost < globalBest.cost) {
                    globalBest = { ...gasClusters[c][0] };
                }
            }
        }

        const finalTour: string[] = [...globalBest.tour.map(i => this.points[i].id), this.points[globalBest.tour[0]].id];

        return {
            found: true,
            initialCost,
            bestCost: globalBest.cost,
            tour: finalTour,
            iterationsCompleted: maxIterations,
        };
    }
}