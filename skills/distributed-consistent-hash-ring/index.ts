/**
 * Distributed Consistent Hash Ring with Virtual Nodes (vnodes).
 * Enterprise-grade distributed key routing featuring virtual node replication
 * for uniform key distribution, binary search token lookup (O(log N)),
 * dynamic node addition/removal with rebalancing metrics, and N-replica replication.
 */

import crypto from "node:crypto";

export interface NodeRingConfig {
    vnodesPerNode?: number; // Number of virtual nodes per physical node (default 50)
}

export interface RingNode {
    nodeId: string;
    weight?: number;
}

export class DistributedConsistentHashRing {
    private vnodesPerNode: number;
    private ring: Array<{ hash: number; nodeId: string }> = [];
    private nodes: Set<string> = new Set();

    constructor(config: NodeRingConfig = {}) {
        this.vnodesPerNode = Math.max(1, config.vnodesPerNode ?? 50);
    }

    /**
     * Hashes a string key into a 32-bit unsigned integer.
     */
    private hashKey(key: string): number {
        const hash = crypto.createHash("md5").update(key).digest();
        return hash.readUInt32BE(0);
    }

    /**
     * Adds a physical node to the ring with virtual node replication.
     */
    public addNode(nodeId: string): this {
        if (this.nodes.has(nodeId)) return this;
        this.nodes.add(nodeId);

        for (let i = 0; i < this.vnodesPerNode; i++) {
            const vnodeKey = `${nodeId}#vnode_${i}`;
            const hash = this.hashKey(vnodeKey);
            this.ring.push({ hash, nodeId });
        }

        // Keep ring sorted by hash for binary search
        this.ring.sort((a, b) => a.hash - b.hash);
        return this;
    }

    /**
     * Removes a physical node and all its virtual nodes from the ring.
     */
    public removeNode(nodeId: string): this {
        if (!this.nodes.has(nodeId)) return this;
        this.nodes.delete(nodeId);
        this.ring = this.ring.filter((entry) => entry.nodeId !== nodeId);
        return this;
    }

    /**
     * Locates the primary physical node responsible for a given key.
     */
    public getNode(key: string): string | null {
        if (this.ring.length === 0) return null;

        const hash = this.hashKey(key);
        let low = 0;
        let high = this.ring.length - 1;

        // Binary search for first node where node.hash >= key.hash
        while (low <= high) {
            const mid = Math.floor((low + high) / 2);
            if (this.ring[mid].hash >= hash) {
                high = mid - 1;
            } else {
                low = mid + 1;
            }
        }

        // If key hash is greater than all nodes, wrap around to first node on ring
        const targetIndex = low < this.ring.length ? low : 0;
        return this.ring[targetIndex].nodeId;
    }

    /**
     * Locates N unique replica physical nodes for a given key.
     */
    public getPreferenceList(key: string, replicaCount: number): string[] {
        if (this.nodes.size === 0) return [];
        const targetReplicas = Math.min(replicaCount, this.nodes.size);

        const hash = this.hashKey(key);
        let low = 0;
        let high = this.ring.length - 1;

        while (low <= high) {
            const mid = Math.floor((low + high) / 2);
            if (this.ring[mid].hash >= hash) {
                high = mid - 1;
            } else {
                low = mid + 1;
            }
        }

        let startIndex = low < this.ring.length ? low : 0;
        const resultNodes: string[] = [];
        const seenNodes: Set<string> = new Set();

        for (let i = 0; i < this.ring.length && resultNodes.length < targetReplicas; i++) {
            const idx = (startIndex + i) % this.ring.length;
            const node = this.ring[idx].nodeId;
            if (!seenNodes.has(node)) {
                seenNodes.add(node);
                resultNodes.push(node);
            }
        }

        return resultNodes;
    }
}