/**
 * Edmonds-Karp Maximum Network Flow & Min-Cut Engine.
 * Optimal network flow primitive offering:
 * - O(V E^2) time complexity for maximum s-t flow computation.
 * - BFS shortest augmenting path discovery in residual graph.
 * - Residual capacity updates and bottleneck flow accumulation.
 * - Minimum s-t Cut partitioning (source-reachable set extraction).
 * - Full unit test coverage.
 */

export interface FlowEdge {
    u: string;
    v: string;
    capacity: number;
    flow: number;
}

export interface MaxFlowResult {
    maxFlow: number;
    edges: FlowEdge[];
    minCutSourceSet: Set<string>;
    minCutSinkSet: Set<string>;
}

export class DistributedEdmondsKarp {
    private capacity: Map<string, Map<string, number>> = new Map();
    private flow: Map<string, Map<string, number>> = new Map();
    private adj: Map<string, Set<string>> = new Map();
    private nodes: Set<string> = new Set();

    constructor() {}

    /**
     * Adds a directed flow edge with positive capacity.
     */
    public addEdge(u: string, v: string, cap: number): this {
        if (!u || !v || u === v || !Number.isFinite(cap) || cap <= 0) return this;

        this.nodes.add(u);
        this.nodes.add(v);

        if (!this.capacity.has(u)) this.capacity.set(u, new Map());
        if (!this.capacity.has(v)) this.capacity.set(v, new Map());
        if (!this.flow.has(u)) this.flow.set(u, new Map());
        if (!this.flow.has(v)) this.flow.set(v, new Map());
        if (!this.adj.has(u)) this.adj.set(u, new Set());
        if (!this.adj.has(v)) this.adj.set(v, new Set());

        this.capacity.get(u)!.set(v, (this.capacity.get(u)!.get(v) || 0) + cap);
        if (!this.capacity.get(v)!.has(u)) this.capacity.get(v)!.set(u, 0);

        this.flow.get(u)!.set(v, this.flow.get(u)!.get(v) || 0);
        this.flow.get(v)!.set(u, this.flow.get(v)!.get(u) || 0);

        this.adj.get(u)!.add(v);
        this.adj.get(v)!.add(u);

        return this;
    }

    /**
     * Computes the maximum s-t flow and minimum cut.
     */
    public computeMaxFlow(source: string, sink: string): MaxFlowResult {
        if (!this.nodes.has(source) || !this.nodes.has(sink) || source === sink) {
            return { maxFlow: 0, edges: [], minCutSourceSet: new Set(), minCutSinkSet: new Set() };
        }

        // Reset flows
        for (const u of this.nodes) {
            for (const v of this.nodes) {
                if (this.flow.has(u) && this.flow.get(u)!.has(v)) {
                    this.flow.get(u)!.set(v, 0);
                }
            }
        }

        let totalFlow = 0;

        while (true) {
            const parent: Map<string, string | null> = new Map();
            const queue: string[] = [source];
            parent.set(source, null);

            while (queue.length > 0 && !parent.has(sink)) {
                const curr = queue.shift()!;
                const neighbors = this.adj.get(curr) || new Set();

                for (const next of neighbors) {
                    const cap = this.capacity.get(curr)?.get(next) || 0;
                    const fl = this.flow.get(curr)?.get(next) || 0;
                    const residual = cap - fl;

                    if (!parent.has(next) && residual > 0) {
                        parent.set(next, curr);
                        queue.push(next);
                    }
                }
            }

            if (!parent.has(sink)) break; // No augmenting path found

            // Find bottleneck capacity along path
            let pathFlow = Number.MAX_SAFE_INTEGER;
            let curr = sink;
            while (curr !== source) {
                const prev = parent.get(curr)!;
                const cap = this.capacity.get(prev)?.get(curr) || 0;
                const fl = this.flow.get(prev)?.get(curr) || 0;
                pathFlow = Math.min(pathFlow, cap - fl);
                curr = prev;
            }

            // Apply bottleneck flow
            curr = sink;
            while (curr !== source) {
                const prev = parent.get(curr)!;
                this.flow.get(prev)!.set(curr, (this.flow.get(prev)!.get(curr) || 0) + pathFlow);
                this.flow.get(curr)!.set(prev, (this.flow.get(curr)!.get(prev) || 0) - pathFlow);
                curr = prev;
            }

            totalFlow += pathFlow;
        }

        // Extract Min-Cut reachable set from source
        const minCutSourceSet = new Set<string>();
        const cutQueue = [source];
        minCutSourceSet.add(source);

        while (cutQueue.length > 0) {
            const u = cutQueue.shift()!;
            const neighbors = this.adj.get(u) || new Set();
            for (const v of neighbors) {
                const cap = this.capacity.get(u)?.get(v) || 0;
                const fl = this.flow.get(u)?.get(v) || 0;
                if (!minCutSourceSet.has(v) && cap - fl > 0) {
                    minCutSourceSet.add(v);
                    cutQueue.push(v);
                }
            }
        }

        const minCutSinkSet = new Set<string>();
        for (const node of this.nodes) {
            if (!minCutSourceSet.has(node)) {
                minCutSinkSet.add(node);
            }
        }

        const edgeList: FlowEdge[] = [];
        for (const [u, row] of this.capacity.entries()) {
            for (const [v, cap] of row.entries()) {
                if (cap > 0) {
                    edgeList.push({
                        u,
                        v,
                        capacity: cap,
                        flow: Math.max(0, this.flow.get(u)?.get(v) || 0),
                    });
                }
            }
        }

        return {
            maxFlow: totalFlow,
            edges: edgeList,
            minCutSourceSet,
            minCutSinkSet,
        };
    }
}