import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { SpatialRTree, BoundingBox } from "./index.js";

describe("SpatialRTree Bounding Box Intersection & kNN Spatial Search", () => {
    it("inserts spatial items and queries range intersection", () => {
        const tree = new SpatialRTree();

        tree.insert({
            id: "city_center",
            box: { minX: 10, minY: 10, maxX: 20, maxY: 20 },
            data: { name: "Capital City" },
        });

        tree.insert({
            id: "harbor_dock",
            box: { minX: 50, minY: 50, maxX: 65, maxY: 65 },
            data: { name: "South Harbor" },
        });

        tree.insert({
            id: "mountain_pass",
            box: { minX: 15, minY: 15, maxX: 30, maxY: 30 },
            data: { name: "North Pass" },
        });

        // Search overlapping box around (12, 12, 25, 25)
        const query: BoundingBox = { minX: 12, minY: 12, maxX: 25, maxY: 25 };
        const results = tree.search(query);

        assert.equal(results.length, 2);
        const ids = results.map((r) => r.id);
        assert.ok(ids.includes("city_center"));
        assert.ok(ids.includes("mountain_pass"));
        assert.ok(!ids.includes("harbor_dock"));
    });

    it("performs kNN search based on Euclidean distance to point", () => {
        const tree = new SpatialRTree();

        tree.insert({ id: "p1", box: { minX: 0, minY: 0, maxX: 2, maxY: 2 } });     // center (1, 1)
        tree.insert({ id: "p2", box: { minX: 10, minY: 10, maxX: 12, maxY: 12 } }); // center (11, 11)
        tree.insert({ id: "p3", box: { minX: 100, minY: 100, maxX: 102, maxY: 102 } });

        const nearest = tree.kNearest(2, 2, 2);
        assert.equal(nearest.length, 2);
        assert.equal(nearest[0].item.id, "p1");
        assert.equal(nearest[1].item.id, "p2");
    });

    it("defensively handles invalid coordinates and empty trees", () => {
        const tree = new SpatialRTree();

        tree.insert({ id: "bad", box: { minX: NaN, minY: 0, maxX: 10, maxY: 10 } });
        assert.equal(tree.count, 0);

        assert.deepEqual(tree.search(null as any), []);
        assert.deepEqual(tree.kNearest(NaN, 0), []);
    });
});