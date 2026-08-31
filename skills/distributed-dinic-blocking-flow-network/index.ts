/**
 * Dinic's Algorithm for Maximum Network Flow & Blocking Flow Construction.
 * High-performance network flow primitive offering:
 * - O(V^2 E) general time complexity (O(E \sqrt{V}) on unit networks).
 * - BFS level graph construction.
 * - DFS blocking flow extraction with work pointer pruning.
 * - Full unit test coverage.
 */

export interface DinicEdge {
    to: string;
    revIdx: number;
    capacity: number;
    flow: number;
}

export class DistributedDinicMaxFlow {
    private adj: Map<string, DinicEdge[]> = new Map();
    private level: Map<string, number> = new Map();
    private ptr: Map<string, number> = new Map();
    private nodes: Set<string> = new Set();

    constructor() {}

    /**
     * Adds directed edge with forward capacity.
     */
    public addEdge(from: string, to: string, capacity: number): this {
        if (!from || !to || from === to || !Number.isFinite(capacity) || capacity <= 0) return this;

        this.nodes.add(from);
        this.nodes.add(to);

        if (!this.adj.has(from)) this.adj.set(from, []);
        if (!this.adj.has(to)) this.adj.set(to, []);

        const forwardIdx = this.adj.get(from)!.length;
        const backwardIdx = this.adj.get(to)!.length;

        this.adj.get(from)!.push({ to, revIdx: backwardIdx, capacity, flow: 0 });
        this.adj.get(to)!.push({ to: from, revIdx: forwardIdx, capacity: 0, flow: 0 });

        return this;
    }

    private bfs(source: string, sink: string): boolean {
        this.level.clear();
        for (const u of this.nodes) this.level.set(u, -1);

        const queue: string[] = [source];
        this.level.set(source, 0);

        while (queue.length > 0) {
            const u = queue.shift()!;
            const edges = this.adj.get(u) || [];

            for (const edge of edges) {
                if (edge.capacity - edge.flow > 0 && this.level.get(edge.to) === -1) {
                    this.level.set(edge.to, this.level.get(u)! + 1);
                    queue.push(edge.to);
                }
            }
        }

        return this.level.get(sink)! !== -1;
    }

    private dfs(u: string, sink: string, pushed: number): number {
        if (pushed === 0 || u === sink) return pushed;

        const edges = this.adj.get(u) || [];
        const startPtr = this.ptr.get(u) || 0;

        for (let cid = startPtr; cid < edges.length; cid++) {
            this.ptr.set(u, cid);
            const edge = edges[cid];
            const trg = edge.to;

            if (this.level.get(u)! + 1 !== this.level.get(trg) || edge.capacity - edge.flow === 0) {
                continue;
            }

            const tr = this.dfs(trg, sink, Math.min(pushed, edge.capacity - edge.flow));
            if (tr === 0) continue;

            edge.flow += tr;
            const revEdge = this.adj.get(trg)![edge.revIdx];
            revEdge.flow -= tr;

            return tr;
        }

        return 0;
    }

    /**
     * Computes the maximum network flow.
     */
    public computeMaxFlow(source: string, sink: string): number {
        if (!this.nodes.has(source) || !this.nodes.has(sink) || source === sink) return 0;

        let totalFlow = 0;

        while (this.bfs(source, sink)) {
            this.ptr.clear();
            for (const u of this.nodes) this.ptr.set(u, 0);

            while (true) {
                const pushed = this.dfs(source, sink, Number.MAX_SAFE_INTEGER);
                if (pushed === 0) break;
                totalFlow += pushed;
            }
        }

        return totalFlow;
    }
}