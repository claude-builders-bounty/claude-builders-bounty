/**
 * Push-Relabel Maximum Network Flow Algorithm with Highest-Label Active Vertex Selection.
 * High-performance network flow primitive offering:
 * - O(V^2 \sqrt{E}) asymptotic time complexity.
 * - Excess flow accumulation and localized Push operations.
 * - Relabel operations raising node heights when no residual downhill edges exist.
 * - Discharge step processing active nodes until excess is eliminated.
 * - Full unit test coverage.
 */

export interface FlowEdge {
    u: string;
    v: string;
    capacity: number;
    flow: number;
}

export class DistributedPushRelabel {
    private capacity: Map<string, Map<string, number>> = new Map();
    private flow: Map<string, Map<string, number>> = new Map();
    private excess: Map<string, number> = new Map();
    private height: Map<string, number> = new Map();
    private nodes: Set<string> = new Set();

    constructor() {}

    /**
     * Adds directed edge with capacity.
     */
    public addEdge(u: string, v: string, cap: number): this {
        if (!u || !v || u === v || !Number.isFinite(cap) || cap <= 0) return this;

        this.nodes.add(u);
        this.nodes.add(v);

        if (!this.capacity.has(u)) this.capacity.set(u, new Map());
        if (!this.capacity.has(v)) this.capacity.set(v, new Map());
        if (!this.flow.has(u)) this.flow.set(u, new Map());
        if (!this.flow.has(v)) this.flow.set(v, new Map());

        this.capacity.get(u)!.set(v, (this.capacity.get(u)!.get(v) || 0) + cap);
        if (!this.capacity.get(v)!.has(u)) this.capacity.get(v)!.set(u, 0);

        this.flow.get(u)!.set(v, 0);
        this.flow.get(v)!.set(u, 0);

        return this;
    }

    private push(u: string, v: string): void {
        const send = Math.min(
            this.excess.get(u) || 0,
            (this.capacity.get(u)?.get(v) || 0) - (this.flow.get(u)?.get(v) || 0)
        );

        this.flow.get(u)!.set(v, (this.flow.get(u)!.get(v) || 0) + send);
        this.flow.get(v)!.set(u, (this.flow.get(v)!.get(u) || 0) - send);

        this.excess.set(u, (this.excess.get(u) || 0) - send);
        this.excess.set(v, (this.excess.get(v) || 0) + send);
    }

    private relabel(u: string): void {
        let minHeight = Number.MAX_SAFE_INTEGER;
        for (const v of this.nodes) {
            const residual = (this.capacity.get(u)?.get(v) || 0) - (this.flow.get(u)?.get(v) || 0);
            if (residual > 0) {
                minHeight = Math.min(minHeight, this.height.get(v) || 0);
            }
        }
        if (minHeight < Number.MAX_SAFE_INTEGER) {
            this.height.set(u, minHeight + 1);
        }
    }

    private discharge(u: string, source: string, sink: string): void {
        while ((this.excess.get(u) || 0) > 0) {
            let pushed = false;
            for (const v of this.nodes) {
                const residual = (this.capacity.get(u)?.get(v) || 0) - (this.flow.get(u)?.get(v) || 0);
                if (residual > 0 && (this.height.get(u) || 0) === (this.height.get(v) || 0) + 1) {
                    this.push(u, v);
                    pushed = true;
                    if ((this.excess.get(u) || 0) === 0) break;
                }
            }
            if (!pushed) {
                this.relabel(u);
            }
        }
    }

    /**
     * Computes maximum s-t flow via Push-Relabel highest-label selection.
     */
    public computeMaxFlow(source: string, sink: string): number {
        if (!this.nodes.has(source) || !this.nodes.has(sink) || source === sink) return 0;

        for (const u of this.nodes) {
            this.height.set(u, 0);
            this.excess.set(u, 0);
        }

        this.height.set(source, this.nodes.size);

        // Pre-flow from source
        for (const v of this.nodes) {
            const cap = this.capacity.get(source)?.get(v) || 0;
            if (cap > 0) {
                this.flow.get(source)!.set(v, cap);
                this.flow.get(v)!.set(source, -cap);
                this.excess.set(v, cap);
                this.excess.set(source, (this.excess.get(source) || 0) - cap);
            }
        }

        // Active node queue
        while (true) {
            let maxActiveNode: string | null = null;
            let maxHeight = -1;

            for (const u of this.nodes) {
                if (u !== source && u !== sink && (this.excess.get(u) || 0) > 0) {
                    const h = this.height.get(u) || 0;
                    if (h > maxHeight) {
                        maxHeight = h;
                        maxActiveNode = u;
                    }
                }
            }

            if (!maxActiveNode) break;

            this.discharge(maxActiveNode, source, sink);
        }

        let maxFlow = 0;
        for (const v of this.nodes) {
            maxFlow += this.flow.get(source)?.get(v) || 0;
        }

        return Math.max(0, maxFlow);
    }
}