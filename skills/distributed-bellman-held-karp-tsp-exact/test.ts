import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedBellmanHeldKarpTSP } from "./index.js";

describe("DistributedBellmanHeldKarpTSP Exact Tour Optimization", () => {
    it("computes exact optimal Hamiltonian cycle for 4 cities in O(n^2 2^n) time", () => {
        const tsp = new DistributedBellmanHeldKarpTSP();

        // 4 Cities: A, B, C, D
        const cities = ["A", "B", "C", "D"];
        const matrix: Record<string, Record<string, number>> = {
            A: { A: 0, B: 10, C: 15, D: 20 },
            B: { A: 10, B: 0, C: 35, D: 25 },
            C: { A: 15, B: 35, C: 0, D: 30 },
            D: { A: 20, B: 25, C: 30, D: 0 },
        };

        tsp.setCitiesAndDistances(cities, (u, v) => matrix[u][v]);

        const result = tsp.computeOptimalTour("A");
        assert.equal(result.found, true);
        assert.equal(result.citiesCount, 4);

        // Optimal tour: A -> B (10) -> D (25) -> C (30) -> A (15) = 80
        assert.equal(result.minCost, 80);
        assert.equal(result.tour[0], "A");
        assert.equal(result.tour[result.tour.length - 1], "A");
        assert.equal(result.tour.length, 5);
    });

    it("handles single city and disconnected graphs", () => {
        const single = new DistributedBellmanHeldKarpTSP();
        single.setCitiesAndDistances(["A"], () => 0);
        const resSingle = single.computeOptimalTour();
        assert.equal(resSingle.found, true);
        assert.equal(resSingle.minCost, 0);

        const disconn = new DistributedBellmanHeldKarpTSP();
        disconn.setCitiesAndDistances(["X", "Y"], () => Number.POSITIVE_INFINITY);
        assert.equal(disconn.computeOptimalTour().found, false);
    });

    it("guards against empty inputs and excessive city counts", () => {
        const empty = new DistributedBellmanHeldKarpTSP();
        assert.equal(empty.computeOptimalTour().found, false);

        const tooBig = new DistributedBellmanHeldKarpTSP();
        const bigCities = Array.from({ length: 25 }, (_, i) => `City_${i}`);
        tooBig.setCitiesAndDistances(bigCities, () => 1);
        assert.throws(() => tooBig.computeOptimalTour(), /designed for n <= 20/);
    });
});