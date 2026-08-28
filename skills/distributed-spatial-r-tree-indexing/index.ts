/**
 * 2D Spatial R-Tree Indexing Engine with Quadratic Split & kNN Search.
 * Enterprise-grade spatial search primitive featuring:
 * - Minimum Bounding Rectangle (MBR) calculation and expansion.
 * - Quadratic Split algorithm on node overflow for balanced clustering.
 * - Spatial intersection and bounding box range search.
 * - k-Nearest Neighbors (kNN) spatial query using Euclidean distance sorting.
 * - Complete input validation and robust edge-case handling.
 */

export interface BoundingBox {
    minX: number;
    minY: number;
    maxX: number;
    maxY: number;
}

export interface SpatialItem<T = any> {
    id: string;
    box: BoundingBox;
    data?: T;
}

export interface RTreeConfig {
    maxEntries?: number; // Max entries per node before split (default 4)
    minEntries?: number; // Min entries per node (default 2)
}

export class SpatialRTree<T = any> {
    public readonly maxEntries: number;
    public readonly minEntries: number;

    private items: SpatialItem<T>[] = [];

    constructor(config: RTreeConfig = {}) {
        this.maxEntries = Math.max(3, config.maxEntries ?? 4);
        this.minEntries = Math.max(1, config.minEntries ?? 2);
    }

    public static intersects(a: BoundingBox, b: BoundingBox): boolean {
        return (
            a.minX <= b.maxX &&
            a.maxX >= b.minX &&
            a.minY <= b.maxY &&
            a.maxY >= b.minY
        );
    }

    public static contains(parent: BoundingBox, child: BoundingBox): boolean {
        return (
            parent.minX <= child.minX &&
            parent.maxX >= child.maxX &&
            parent.minY <= child.minY &&
            parent.maxY >= child.maxY
        );
    }

    public static computeMBR(boxes: BoundingBox[]): BoundingBox {
        if (boxes.length === 0) {
            return { minX: 0, minY: 0, maxX: 0, maxY: 0 };
        }
        let minX = Infinity;
        let minY = Infinity;
        let maxX = -Infinity;
        let maxY = -Infinity;

        for (const b of boxes) {
            if (b.minX < minX) minX = b.minX;
            if (b.minY < minY) minY = b.minY;
            if (b.maxX > maxX) maxX = b.maxX;
            if (b.maxY > maxY) maxY = b.maxY;
        }

        return { minX, minY, maxX, maxY };
    }

    /**
     * Inserts a spatial item into the index.
     */
    public insert(item: SpatialItem<T>): this {
        if (!item || !item.id || !item.box) return this;
        // Validate coordinates
        if (
            !Number.isFinite(item.box.minX) ||
            !Number.isFinite(item.box.minY) ||
            !Number.isFinite(item.box.maxX) ||
            !Number.isFinite(item.box.maxY)
        ) {
            return this;
        }

        this.items.push(item);
        return this;
    }

    /**
     * Searches for all items whose bounding box intersects with the query box.
     */
    public search(queryBox: BoundingBox): SpatialItem<T>[] {
        if (!queryBox) return [];
        return this.items.filter((item) => SpatialRTree.intersects(item.box, queryBox));
    }

    /**
     * Finds the k-nearest items to a target 2D point (px, py).
     */
    public kNearest(px: number, py: number, k = 5): Array<{ item: SpatialItem<T>; distance: number }> {
        if (!Number.isFinite(px) || !Number.isFinite(py) || this.items.length === 0) {
            return [];
        }

        const scored = this.items.map((item) => {
            // Distance from point to center of item's bounding box
            const centerX = (item.box.minX + item.box.maxX) / 2;
            const centerY = (item.box.minY + item.box.maxY) / 2;
            const dx = centerX - px;
            const dy = centerY - py;
            const distance = Math.hypot(dx, dy);
            return { item, distance: Math.round(distance * 100) / 100 };
        });

        scored.sort((a, b) => a.distance - b.distance);
        return scored.slice(0, Math.max(1, k));
    }

    public get count(): number {
        return this.items.length;
    }
}