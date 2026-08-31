import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedMultiSourceVoronoi } from "./index.js";

describe("DistributedMultiSourceVoronoi Graph Partitioning", () => {
    it("partitions graph into Voronoi cells based on shortest multi-source Dijkstra distances", () => {
        const voronoi = new DistributedMultiSourceVoronoi();

        // Line graph: S1 - A (2) - B (2) - M (2) - C (2) - D (2) - S2
        voronoi.addEdge("S1", "A", 2);
        voronoi.addEdge("A", "S1", 2);
        voronoi.addEdge("A", "B", 2);
        voronoi.addEdge("B", "A", 2);
        voronoi.addEdge("B", "M", 2);
        voronoi.addEdge("M", "B", 2);

        voronoi.addEdge("S2", "D", 2);
        voronoi.addEdge("D", "S2", 2);
        voronoi.addEdge("D", "C", 2);
        voronoi.addEdge("C", "D", 2);
        voronoi.addEdge("C", "M", 2);
        voronoi.addEdge("M", "C", 2);

        const result = voronoi.computeVoronoiPartition(["S1", "S2"]);
        assert.equal(result.unreachableNodes.length, 0);

        // S1 owns S1, A, B
        assert.equal(result.nodeNearestSource.get("A"), "S1");
        assert.equal(result.nodeNearestSource.get("B"), "S1");
        assert.equal(result.nodeShortestDist.get("B"), 4);

        // S2 owns S2, D, C
        assert.equal(result.nodeNearestSource.get("D"), "S2");
        assert.equal(result.nodeNearestSource.get("C"), "S2");

        // M is equidistant (6 from S1, 6 from S2), tie-breaks to S1
        assert.equal(result.nodeNearestSource.get("M"), "S1");
        assert.equal(result.nodeShortestDist.get("M"), 6);
    });

    it("correctly flags disconnected unreachable nodes", () => {
        const voronoi = new DistributedMultiSourceVoronoi();

        voronoi.addEdge("S1", "A", 3);
        voronoi.addEdge("Isolated1", "Isolated2", 5);

        const result = voronoi.computeVoronoiPartition(["S1"]);
        assert.equal(result.nodeNearestSource.get("A"), "S1");
        assert.equal(result.unreachableNodes.includes("Isolated1"), true);
        assert.equal(result.unreachableNodes.includes("Isolated2"), true);
    });

    it("defensively handles empty sources list and invalid edge inputs", () => {
        const voronoi = new DistributedMultiSourceVoronoi();

        voronoi.addEdge("X", "Y", 10);
        voronoi.addEdge("X", "X", 5); // Self loop rejected

        const empty = voronoi.computeVoronoiPartition([]);
        assert.equal(empty.unreachableNodes.length, 2);
        assert.equal(empty.voronoiCells.size, 0);
    });
});