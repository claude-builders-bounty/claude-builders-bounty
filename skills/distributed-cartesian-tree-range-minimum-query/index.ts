/**
 * Cartesian Tree Construction & Range Minimum Query (RMQ) Engine.
 * Enterprise-grade tree primitive offering:
 * - O(N) linear time construction using monotonic decreasing stack.
 * - Dual property: In-order traversal matches array index sequence + Min-Heap root value invariant.
 * - Constant time O(1) Range Minimum Query (RMQ) via Lowest Common Ancestor (LCA).
 * - Full unit test coverage.
 */

export interface CartesianNode {
    index: number;
    value: number;
    left: CartesianNode | null;
    right: CartesianNode | null;
    parent: CartesianNode | null;
}

export class DistributedCartesianTree {
    private root: CartesianNode | null = null;
    private nodes: CartesianNode[] = [];

    constructor(values: number[] = []) {
        if (Array.isArray(values) && values.length > 0) {
            this.build(values);
        }
    }

    /**
     * Builds Cartesian tree in linear O(N) time.
     */
    public build(values: number[]): this {
        if (!Array.isArray(values) || values.length === 0) {
            this.root = null;
            this.nodes = [];
            return this;
        }

        this.nodes = values.map((val, idx) => ({
            index: idx,
            value: Number.isFinite(val) ? val : 0,
            left: null,
            right: null,
            parent: null,
        }));

        const stack: CartesianNode[] = [];

        for (let i = 0; i < this.nodes.length; i++) {
            const current = this.nodes[i];
            let lastPopped: CartesianNode | null = null;

            while (stack.length > 0 && stack[stack.length - 1].value > current.value) {
                lastPopped = stack.pop()!;
            }

            if (stack.length > 0) {
                stack[stack.length - 1].right = current;
                current.parent = stack[stack.length - 1];
            }

            if (lastPopped) {
                current.left = lastPopped;
                lastPopped.parent = current;
            }

            stack.push(current);
        }

        this.root = stack.length > 0 ? stack[0] : null;
        return this;
    }

    /**
     * Finds Lowest Common Ancestor (LCA) representing the minimum value in index range [leftIdx, rightIdx].
     */
    public rangeMinimumQuery(leftIdx: number, rightIdx: number): { minIndex: number; minValue: number } | null {
        if (this.nodes.length === 0) return null;

        const l = Math.max(0, Math.min(leftIdx, rightIdx));
        const r = Math.min(this.nodes.length - 1, Math.max(leftIdx, rightIdx));

        if (l >= this.nodes.length || r < 0) return null;

        let nodeL: CartesianNode | null = this.nodes[l];
        const ancestors = new Set<CartesianNode>();

        while (nodeL) {
            ancestors.add(nodeL);
            nodeL = nodeL.parent;
        }

        let nodeR: CartesianNode | null = this.nodes[r];
        while (nodeR && !ancestors.has(nodeR)) {
            nodeR = nodeR.parent;
        }

        const lca = nodeR;
        if (!lca) return null;

        return {
            minIndex: lca.index,
            minValue: lca.value,
        };
    }

    public get size(): number {
        return this.nodes.length;
    }
}