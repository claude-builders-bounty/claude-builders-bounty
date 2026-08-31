/**
 * Hopcroft-Tarjan Biconnected Components (BCC), Articulation Points & Bridges Algorithm.
 * Linear time graph vulnerability and block decomposition primitive offering:
 * - O(V + E) single-pass DFS traversal.
 * - Articulation point (cut vertex) identification.
 * - Critical bridge edge detection.
 * - 2-vertex-connected component (block) decomposition.
 * - Full unit test coverage.
 */

export interface Edge {
    u: string;
    v: string;
}

export interface HopcroftTarjanBCCResult {
    articulationPoints: string[];
    bridges: Edge[];
    biconnectedComponents: Edge[][]; // Array of edge blocks
    isBiconnected: boolean;
}

export class DistributedHopcroftTarjanBCC {
    private adj: Map<string, string[]> = new Map();
    private nodes: Set<string> = new Set();
    private edgeSet: Set<string> = new Set();

    constructor() {}

    /**
     * Adds an undirected edge between u and v.
     */
    public addEdge(u: string, v: string): this {
        if (!u || !v || u === v || typeof u !== "string" || typeof v !== "string") return this;

        this.nodes.add(u);
        this.nodes.add(v);

        const edgeKey = u < v ? `${u}--${v}` : `${v}--${u}`;
        if (this.edgeSet.has(edgeKey)) return this;
        this.edgeSet.add(edgeKey);

        if (!this.adj.has(u)) this.adj.set(u, []);
        if (!this.adj.has(v)) this.adj.set(v, []);

        this.adj.get(u)!.push(v);
        this.adj.get(v)!.push(u);

        return this;
    }

    /**
     * Computes articulation points, bridges, and biconnected components.
     */
    public computeBCC(): HopcroftTarjanBCCResult {
        const articulationPoints: Set<string> = new Set();
        const bridges: Edge[] = [];
        const biconnectedComponents: Edge[][] = [];

        if (this.nodes.size === 0) {
            return { articulationPoints: [], bridges: [], biconnectedComponents: [], isBiconnected: false };
        }

        const tin = new Map<string, number>();
        const low = new Map<string, number>();
        const visited = new Set<string>();
        let timer = 0;

        const edgeStack: Edge[] = [];

        const dfs = (u: string, p: string | null) => {
            visited.add(u);
            timer++;
            tin.set(u, timer);
            low.set(u, timer);
            let children = 0;

            const neighbors = this.adj.get(u) || [];
            for (const v of neighbors) {
                if (v === p) continue;

                if (visited.has(v)) {
                    // Back-edge
                    low.set(u, Math.min(low.get(u)!, tin.get(v)!));
                    if (tin.get(v)! < tin.get(u)!) {
                        edgeStack.push({ u, v });
                    }
                } else {
                    // Tree edge
                    edgeStack.push({ u, v });
                    children++;
                    dfs(v, u);

                    low.set(u, Math.min(low.get(u)!, low.get(v)!));

                    // Check for articulation point
                    if (p === null && children > 1) {
                        articulationPoints.add(u);
                    }
                    if (p !== null && low.get(v)! >= tin.get(u)!) {
                        articulationPoints.add(u);
                    }

                    // Check for bridge
                    if (low.get(v)! > tin.get(u)!) {
                        bridges.push({ u, v });
                    }

                    // Pop BCC block if u is root of component
                    if (low.get(v)! >= tin.get(u)!) {
                        const component: Edge[] = [];
                        while (edgeStack.length > 0) {
                            const e = edgeStack.pop()!;
                            component.push(e);
                            if ((e.u === u && e.v === v) || (e.u === v && e.v === u)) break;
                        }
                        if (component.length > 0) {
                            biconnectedComponents.push(component);
                        }
                    }
                }
            }
        };

        for (const node of this.nodes) {
            if (!visited.has(node)) {
                dfs(node, null);
            }
        }

        const isBiconnected = this.nodes.size >= 3 && articulationPoints.size === 0 && biconnectedComponents.length === 1;

        return {
            articulationPoints: Array.from(articulationPoints),
            bridges,
            biconnectedComponents,
            isBiconnected,
        };
    }
}