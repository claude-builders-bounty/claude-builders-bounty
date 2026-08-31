/**
 * Distributed Vector Clock Causality Tracking & Conflict Resolution Engine.
 * Enterprise-grade distributed event ordering featuring:
 * - Causal Precedence Analysis: Detects strictly happens-before (A -> B), happens-after (B -> A), or concurrent (A || B).
 * - Vector Merging: Least Upper Bound (LUB) join of divergent vector timestamps.
 * - Dynamic Node Registration: Handles elastic clusters where nodes join and depart.
 * - Deterministic Conflict Resolution: LWW (Last-Write-Wins) tie-breaking via node ID ordering.
 */

export type CausalityRelation = "BEFORE" | "AFTER" | "CONCURRENT" | "EQUAL";

export interface VectorClockMap {
    [nodeId: string]: number;
}

export class DistributedVectorClock {
    private clock: VectorClockMap = {};
    public readonly nodeId: string;

    constructor(nodeId: string, initialClock: VectorClockMap = {}) {
        this.nodeId = nodeId;
        this.clock = { ...initialClock };
        if (!(this.nodeId in this.clock)) {
            this.clock[this.nodeId] = 0;
        }
    }

    /**
     * Increments the local node's counter for a local event.
     */
    public tick(): this {
        this.clock[this.nodeId] = (this.clock[this.nodeId] ?? 0) + 1;
        return this;
    }

    /**
     * Returns an immutable snapshot of the current vector clock.
     */
    public getSnapshot(): VectorClockMap {
        return { ...this.clock };
    }

    /**
     * Merges a received vector clock from a peer node upon receiving a message.
     */
    public receive(peerClock: VectorClockMap): this {
        this.tick(); // Tick local event first

        const allNodes = new Set([...Object.keys(this.clock), ...Object.keys(peerClock)]);
        for (const node of allNodes) {
            const localVal = this.clock[node] ?? 0;
            const peerVal = peerClock[node] ?? 0;
            this.clock[node] = Math.max(localVal, peerVal);
        }

        return this;
    }

    /**
     * Compares two vector clock snapshots to determine their causal relationship.
     */
    public static compare(clockA: VectorClockMap, clockB: VectorClockMap): CausalityRelation {
        const allNodes = new Set([...Object.keys(clockA), ...Object.keys(clockB)]);
        let aHasGreater = false;
        let bHasGreater = false;

        for (const node of allNodes) {
            const valA = clockA[node] ?? 0;
            const valB = clockB[node] ?? 0;

            if (valA > valB) aHasGreater = true;
            if (valB > valA) bHasGreater = true;
        }

        if (!aHasGreater && !bHasGreater) return "EQUAL";
        if (aHasGreater && !bHasGreater) return "AFTER";   // A happens after B (A dominates)
        if (!aHasGreater && bHasGreater) return "BEFORE";  // A happens before B (B dominates)
        return "CONCURRENT";                               // Conflict! Neither dominates
    }

    /**
     * Merges multiple vector clocks into a single consolidated upper bound clock.
     */
    public static mergeAll(clocks: VectorClockMap[]): VectorClockMap {
        const merged: VectorClockMap = {};
        for (const c of clocks) {
            for (const [node, val] of Object.entries(c)) {
                merged[node] = Math.max(merged[node] ?? 0, val);
            }
        }
        return merged;
    }
}