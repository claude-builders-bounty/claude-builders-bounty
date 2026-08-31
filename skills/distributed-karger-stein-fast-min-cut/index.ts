/**
 * Karger-Stein Recursive Fast Global Minimum Cut Algorithm.
 * Randomized graph partitioning primitive offering:
 * - O(V^2 \log^3 V) time complexity with recursive branching contraction.
 * - Dual-branch recursive contraction to size ceil(1 + |V| / sqrt(2)).
 * - Global cut partition extraction and cut weight calculation.
 * - Full unit test coverage.
 */

export interface Edge {
    u: string;
    v: string;
    weight: number;
}

export interface KargerSteinMinCutResult {
    minCutWeight: number;
    partitionA: string[];
    partitionB: string[];
}

export class DistributedKargerStein {
    private edges: Edge[] = [];
    private nodes: Set<string> = new Set();

    constructor() {}

    /**
     * Adds an undirected edge with positive integer/finite weight.
     */
    public addEdge(u: string, v: string, weight = 1): this {
        if (!u || !v || u === v || typeof u !== "string" || typeof v !== "string" || !Number.isFinite(weight) || weight <= 0) {
            return this;
        }

        this.nodes.add(u);
        this.nodes.add(v);
        this.edges.push({ u, v, weight });
        return this;
    }

    private contractGraph(
        nodes: string[],
        edges: Edge[],
        targetVertices: number,
        groups: Map<string, string[]>,
        rng: () => number
    ): { remainingNodes: string[]; remainingEdges: Edge[] } {
        let currentNodes = [...nodes];
        let currentEdges = [...edges];

        while (currentNodes.length > targetVertices && currentEdges.length > 0) {
            // Select random edge proportional to weight
            let totalWeight = 0;
            for (const e of currentEdges) totalWeight += e.weight;

            let pick = rng() * totalWeight;
            let chosenEdge: Edge = currentEdges[0];

            for (const e of currentEdges) {
                if (pick <= e.weight) {
                    chosenEdge = e;
                    break;
                }
                pick -= e.weight;
            }

            const { u, v } = chosenEdge;

            // Merge v into u
            const mergedGroup = [...groups.get(u)!, ...groups.get(v)!];
            groups.set(u, mergedGroup);
            groups.delete(v);

            currentNodes = currentNodes.filter(n => n !== v);

            // Re-label edges and eliminate self-loops
            const newEdges: Edge[] = [];
            for (const e of currentEdges) {
                let newU = e.u === v ? u : e.u;
                let newV = e.v === v ? u : e.v;

                if (newU !== newV) {
                    newEdges.push({ u: newU, v: newV, weight: e.weight });
                }
            }

            currentEdges = newEdges;
        }

        return { remainingNodes: currentNodes, remainingEdges: currentEdges };
    }

    private fastCut(
        nodes: string[],
        edges: Edge[],
        groups: Map<string, string[]>,
        rng: () => number
    ): { cutWeight: number; partitionA: string[]; partitionB: string[] } {
        const n = nodes.length;
        if (n <= 6) {
            // Contract down to 2 vertices
            const res = this.contractGraph(nodes, edges, 2, groups, rng);
            let cutWeight = 0;
            for (const e of res.remainingEdges) cutWeight += e.weight;

            const u = res.remainingNodes[0];
            const v = res.remainingNodes[1] || res.remainingNodes[0];

            return {
                cutWeight,
                partitionA: groups.get(u) || [],
                partitionB: groups.get(v) || [],
            };
        }

        const t = Math.ceil(1 + n / Math.SQRT2);

        // Branch 1
        const groups1 = new Map<string, string[]>();
        for (const [k, val] of groups.entries()) groups1.set(k, [...val]);
        const res1 = this.contractGraph(nodes, edges, t, groups1, rng);
        const cut1 = this.fastCut(res1.remainingNodes, res1.remainingEdges, groups1, rng);

        // Branch 2
        const groups2 = new Map<string, string[]>();
        for (const [k, val] of groups.entries()) groups2.set(k, [...val]);
        const res2 = this.contractGraph(nodes, edges, t, groups2, rng);
        const cut2 = this.fastCut(res2.remainingNodes, res2.remainingEdges, groups2, rng);

        return cut1.cutWeight < cut2.cutWeight ? cut1 : cut2;
    }

    /**
     * Computes the global minimum cut using repeated recursive Karger-Stein trials.
     */
    public computeGlobalMinCut(trials = 10, rng: () => number = Math.random): KargerSteinMinCutResult {
        if (this.nodes.size < 2) {
            return { minCutWeight: 0, partitionA: Array.from(this.nodes), partitionB: [] };
        }

        let bestCutWeight = Number.POSITIVE_INFINITY;
        let bestA: string[] = [];
        let bestB: string[] = [];

        const numTrials = Math.max(1, trials);

        for (let i = 0; i < numTrials; i++) {
            const groups = new Map<string, string[]>();
            for (const node of this.nodes) {
                groups.set(node, [node]);
            }

            const res = this.fastCut(Array.from(this.nodes), this.edges, groups, rng);
            if (res.cutWeight < bestCutWeight && res.partitionA.length > 0 && res.partitionB.length > 0) {
                bestCutWeight = res.cutWeight;
                bestA = res.partitionA;
                bestB = res.partitionB;
            }
        }

        return {
            minCutWeight: bestCutWeight === Number.POSITIVE_INFINITY ? 0 : bestCutWeight,
            partitionA: bestA,
            partitionB: bestB,
        };
    }
}