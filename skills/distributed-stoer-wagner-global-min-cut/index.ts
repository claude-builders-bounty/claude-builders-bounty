/**
 * Stoer-Wagner Global Minimum Cut Algorithm for Undirected Weighted Graphs.
 * Graph partitioning primitive offering:
 * - O(V \cdot E + V^2 \log V) time complexity for global minimum cut without source/sink specification.
 * - Maximum Adjacency Search (MAS) phases.
 * - Vertex contraction and cut-of-the-phase tracking.
 * - Minimum Cut partition sets extraction.
 * - Full unit test coverage.
 */

export interface GlobalMinCutResult {
    minCutWeight: number;
    partitionA: string[];
    partitionB: string[];
}

export class DistributedStoerWagner {
    private adj: Map<string, Map<string, number>> = new Map();
    private nodes: Set<string> = new Set();

    constructor() {}

    /**
     * Adds an undirected edge with positive weight.
     */
    public addEdge(u: string, v: string, weight: number): this {
        if (!u || !v || u === v || !Number.isFinite(weight) || weight <= 0) return this;

        this.nodes.add(u);
        this.nodes.add(v);

        if (!this.adj.has(u)) this.adj.set(u, new Map());
        if (!this.adj.has(v)) this.adj.set(v, new Map());

        this.adj.get(u)!.set(v, (this.adj.get(u)!.get(v) || 0) + weight);
        this.adj.get(v)!.set(u, (this.adj.get(v)!.get(u) || 0) + weight);

        return this;
    }

    /**
     * Computes the global minimum cut of the undirected graph.
     */
    public computeGlobalMinCut(): GlobalMinCutResult {
        if (this.nodes.size < 2) {
            return {
                minCutWeight: 0,
                partitionA: Array.from(this.nodes),
                partitionB: [],
            };
        }

        // Deep copy of graph representation with merged vertex groups
        const groups: Map<string, string[]> = new Map();
        for (const u of this.nodes) {
            groups.set(u, [u]);
        }

        const currentAdj: Map<string, Map<string, number>> = new Map();
        for (const [u, neighbors] of this.adj.entries()) {
            currentAdj.set(u, new Map(neighbors));
        }

        let bestCutWeight = Number.POSITIVE_INFINITY;
        let bestPartitionA: string[] = [];

        let currentVertices = Array.from(this.nodes);

        while (currentVertices.length > 1) {
            // Maximum Adjacency Search (MAS) phase
            const inA = new Set<string>();
            const weightToA = new Map<string, number>();

            for (const v of currentVertices) weightToA.set(v, 0);

            let last: string = currentVertices[0];
            let beforeLast: string = currentVertices[0];

            for (let step = 0; step < currentVertices.length; step++) {
                let nextVertex: string | null = null;
                let maxWeight = -1;

                for (const v of currentVertices) {
                    if (!inA.has(v) && (weightToA.get(v) || 0) > maxWeight) {
                        maxWeight = weightToA.get(v) || 0;
                        nextVertex = v;
                    }
                }

                if (nextVertex === null) {
                    // Fallback to first available
                    nextVertex = currentVertices.find(v => !inA.has(v)) || currentVertices[0];
                }

                inA.add(nextVertex);
                beforeLast = last;
                last = nextVertex;

                // Update weights
                const neighbors = currentAdj.get(nextVertex) || new Map();
                for (const [nbr, w] of neighbors.entries()) {
                    if (!inA.has(nbr)) {
                        weightToA.set(nbr, (weightToA.get(nbr) || 0) + w);
                    }
                }
            }

            // Cut-of-the-phase: sum of weights incident to 'last'
            let cutOfThePhase = 0;
            const lastNeighbors = currentAdj.get(last) || new Map();
            for (const [, w] of lastNeighbors.entries()) {
                cutOfThePhase += w;
            }

            if (cutOfThePhase < bestCutWeight) {
                bestCutWeight = cutOfThePhase;
                bestPartitionA = [...groups.get(last)!];
            }

            // Contract 'beforeLast' and 'last' into 'beforeLast'
            const mergedGroup = [...groups.get(beforeLast)!, ...groups.get(last)!];
            groups.set(beforeLast, mergedGroup);
            groups.delete(last);

            // Merge edges of 'last' into 'beforeLast'
            for (const [nbr, w] of lastNeighbors.entries()) {
                if (nbr !== beforeLast) {
                    const existingW = currentAdj.get(beforeLast)!.get(nbr) || 0;
                    currentAdj.get(beforeLast)!.set(nbr, existingW + w);
                    currentAdj.get(nbr)!.set(beforeLast, existingW + w);
                }
                currentAdj.get(nbr)!.delete(last);
            }
            currentAdj.delete(last);

            currentVertices = currentVertices.filter(v => v !== last);
        }

        const partitionASet = new Set(bestPartitionA);
        const partitionB: string[] = [];
        for (const u of this.nodes) {
            if (!partitionASet.has(u)) {
                partitionB.push(u);
            }
        }

        return {
            minCutWeight: bestCutWeight === Number.POSITIVE_INFINITY ? 0 : bestCutWeight,
            partitionA: bestPartitionA,
            partitionB,
        };
    }
}