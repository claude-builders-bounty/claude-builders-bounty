/**
 * Consistent Hashing with Bounded Loads (Google Mirrokni Algorithm).
 * Enterprise-grade distributed load balancer avoiding hotspot node overloads:
 * - Hash Ring with Virtual Nodes (vnodes) for uniform key distribution.
 * - Dynamic Load Capacity Bound: Cap per node = ceil((1 + epsilon) * (TotalKeys / ActiveNodes)).
 * - Graceful Cascading: If target node is at capacity, item cascades to next clockwise successor.
 * - Dynamic Node Additions/Removals with deterministic re-assignment.
 */

export interface BoundedLoadsConfig {
    vnodesPerNode?: number; // Virtual nodes multiplier (default 40)
    epsilon?: number;       // Load bound overhead factor (default 0.25 -> max 125% average load)
}

export class DistributedConsistentHashBoundedLoads {
    private vnodesCount: number;
    private epsilon: number;

    // Ring: Array of { hash: number, nodeId: string } sorted by hash
    private ring: Array<{ hash: number; nodeId: string }> = [];
    private activeNodes: Set<string> = new Set();
    // NodeId -> Set of assigned keyIds
    private nodeAssignedKeys: Map<string, Set<string>> = new Map();
    // KeyId -> assigned NodeId
    private keyToNode: Map<string, string> = new Map();

    constructor(config: BoundedLoadsConfig = {}) {
        this.vnodesCount = Math.max(1, config.vnodesPerNode ?? 40);
        this.epsilon = Math.max(0.05, config.epsilon ?? 0.25);
    }

    private hash32(key: string): number {
        let hash = 0x811c9dc5;
        for (let i = 0; i < key.length; i++) {
            hash ^= key.charCodeAt(i);
            hash = Math.imul(hash, 0x01000193);
        }
        return hash >>> 0;
    }

    public addNode(nodeId: string): this {
        if (!nodeId || this.activeNodes.has(nodeId)) return this;

        this.activeNodes.add(nodeId);
        this.nodeAssignedKeys.set(nodeId, new Set());

        for (let i = 0; i < this.vnodesCount; i++) {
            const vnodeKey = `${nodeId}#vn#${i}`;
            const hash = this.hash32(vnodeKey);
            this.ring.push({ hash, nodeId });
        }

        this.ring.sort((a, b) => a.hash - b.hash);
        return this;
    }

    public removeNode(nodeId: string): this {
        if (!this.activeNodes.has(nodeId)) return this;

        this.activeNodes.delete(nodeId);
        this.ring = this.ring.filter((entry) => entry.nodeId !== nodeId);

        const keysToReassign = Array.from(this.nodeAssignedKeys.get(nodeId) ?? []);
        this.nodeAssignedKeys.delete(nodeId);

        for (const k of keysToReassign) {
            this.keyToNode.delete(k);
            this.assignKey(k);
        }

        return this;
    }

    public getCapacityLimit(totalKeys: number): number {
        const n = this.activeNodes.size;
        if (n === 0) return 0;
        const avg = totalKeys / n;
        return Math.max(1, Math.ceil((1 + this.epsilon) * avg));
    }

    /**
     * Assigns a key to a node respecting the bounded load capacity limit.
     */
    public assignKey(key: string): string | null {
        if (this.activeNodes.size === 0 || !key) return null;

        if (this.keyToNode.has(key)) {
            return this.keyToNode.get(key)!;
        }

        const totalKeys = this.keyToNode.size + 1;
        const capacityLimit = this.getCapacityLimit(totalKeys);

        const keyHash = this.hash32(key);

        // Find primary starting index in ring
        let startIndex = this.ring.findIndex((entry) => entry.hash >= keyHash);
        if (startIndex === -1) startIndex = 0;

        // Cascade clockwise until finding a node below capacity limit
        const ringLen = this.ring.length;
        for (let i = 0; i < ringLen; i++) {
            const candidateNode = this.ring[(startIndex + i) % ringLen].nodeId;
            const currentLoad = this.nodeAssignedKeys.get(candidateNode)?.size ?? 0;

            if (currentLoad < capacityLimit) {
                this.nodeAssignedKeys.get(candidateNode)!.add(key);
                this.keyToNode.set(key, candidateNode);
                return candidateNode;
            }
        }

        // Fallback to least loaded node if all exceeded
        let minNode = Array.from(this.activeNodes)[0];
        let minLoad = Infinity;
        for (const node of this.activeNodes) {
            const load = this.nodeAssignedKeys.get(node)?.size ?? 0;
            if (load < minLoad) {
                minLoad = load;
                minNode = node;
            }
        }

        this.nodeAssignedKeys.get(minNode)!.add(key);
        this.keyToNode.set(key, minNode);
        return minNode;
    }

    public getNodeLoad(nodeId: string): number {
        return this.nodeAssignedKeys.get(nodeId)?.size ?? 0;
    }
}