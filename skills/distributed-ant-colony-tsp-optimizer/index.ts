/**
 * Ant Colony System (ACS) Pheromone Metaheuristic Optimization for Traveling Salesperson Problem (TSP).
 * Swarm intelligence optimization primitive offering:
 * - O(I \cdot A \cdot n^2) polynomial time complexity across I iterations and A artificial ants.
 * - Pheromone trail deposition and evaporation: \tau = (1-\rho)\tau + \Delta \tau.
 * - Heuristic transition probability with distance visibility weights \eta = 1/d.
 * - Full unit test coverage.
 */

export interface Point2D {
    id: string;
    x: number;
    y: number;
}

export interface AntColonyTSPResult {
    found: boolean;
    bestCost: number;
    tour: string[];
    iterationsCompleted: number;
}

export class DistributedAntColonyTSP {
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

    /**
     * Optimizes tour using Ant Colony Optimization.
     */
    public optimize(
        numAnts = 10,
        iterations = 50,
        alpha = 1.0, // Pheromone importance
        beta = 2.0,  // Distance heuristic importance
        evaporationRate = 0.1,
        q0 = 0.9,
        rng: () => number = Math.random
    ): AntColonyTSPResult {
        const n = this.points.length;
        if (n === 0) {
            return { found: false, bestCost: 0, tour: [], iterationsCompleted: 0 };
        }

        if (n <= 2) {
            const indices = Array.from({ length: n }, (_, i) => i);
            const cost = this.computeTourCost(indices);
            return {
                found: true,
                bestCost: cost,
                tour: [...indices.map(i => this.points[i].id), indices.length > 0 ? this.points[indices[0]].id : ""].filter(Boolean),
                iterationsCompleted: 0,
            };
        }

        // Distance & Heuristic Matrix
        const dist: number[][] = Array.from({ length: n }, () => Array(n).fill(0));
        const eta: number[][] = Array.from({ length: n }, () => Array(n).fill(0));

        for (let i = 0; i < n; i++) {
            for (let j = 0; j < n; j++) {
                if (i !== j) {
                    const d = this.getDistance(this.points[i], this.points[j]);
                    dist[i][j] = d;
                    eta[i][j] = 1.0 / Math.max(1e-6, d);
                }
            }
        }

        // Initialize pheromone matrix
        const initialPheromone = 1.0 / (n * 10);
        const pheromone: number[][] = Array.from({ length: n }, () => Array(n).fill(initialPheromone));

        let bestTour: number[] = Array.from({ length: n }, (_, i) => i);
        let bestCost = this.computeTourCost(bestTour);

        for (let iter = 0; iter < iterations; iter++) {
            const allTours: number[][] = [];
            const allCosts: number[] = [];

            // Build tour for each ant
            for (let ant = 0; ant < numAnts; ant++) {
                const visited = new Set<number>();
                const startCity = Math.floor(rng() * n);
                const tour: number[] = [startCity];
                visited.add(startCity);

                while (tour.length < n) {
                    const curr = tour[tour.length - 1];

                    // Calculate selection probabilities for unvisited cities
                    const unvisited: number[] = [];
                    const probs: number[] = [];
                    let totalProb = 0;

                    for (let j = 0; j < n; j++) {
                        if (!visited.has(j)) {
                            unvisited.push(j);
                            const tau = Math.pow(pheromone[curr][j], alpha);
                            const h = Math.pow(eta[curr][j], beta);
                            const p = tau * h;
                            probs.push(p);
                            totalProb += p;
                        }
                    }

                    let nextCity = unvisited[0];

                    if (rng() < q0 && unvisited.length > 1) {
                        // Exploitation: pick highest probability
                        let maxP = -1;
                        for (let k = 0; k < unvisited.length; k++) {
                            if (probs[k] > maxP) {
                                maxP = probs[k];
                                nextCity = unvisited[k];
                            }
                        }
                    } else {
                        // Exploration: roulette wheel selection
                        let pick = rng() * totalProb;
                        for (let k = 0; k < unvisited.length; k++) {
                            if (pick <= probs[k]) {
                                nextCity = unvisited[k];
                                break;
                            }
                            pick -= probs[k];
                        }
                    }

                    tour.push(nextCity);
                    visited.add(nextCity);
                }

                const cost = this.computeTourCost(tour);
                allTours.push(tour);
                allCosts.push(cost);

                if (cost < bestCost) {
                    bestCost = cost;
                    bestTour = [...tour];
                }
            }

            // Global Pheromone Evaporation and Update
            for (let i = 0; i < n; i++) {
                for (let j = 0; j < n; j++) {
                    pheromone[i][j] *= (1.0 - evaporationRate);
                }
            }

            // Deposit pheromones on the best tour found so far
            const deltaPheromone = 1.0 / Math.max(1e-6, bestCost);
            for (let i = 0; i < n; i++) {
                const from = bestTour[i];
                const to = bestTour[(i + 1) % n];
                pheromone[from][to] += deltaPheromone;
                pheromone[to][from] += deltaPheromone;
            }
        }

        const finalTour: string[] = [...bestTour.map(i => this.points[i].id), this.points[bestTour[0]].id];

        return {
            found: true,
            bestCost,
            tour: finalTour,
            iterationsCompleted: iterations,
        };
    }
}