import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DistributedGeohashClustering } from "./index.js";

describe("DistributedGeohashClustering Geospatial Encoding & Radius Search", () => {
    it("encodes known coordinates to valid GeoHash Base32 strings", () => {
        // Paris coordinates (48.8566, 2.3522) -> GeoHash prefix "u09t"
        const hash = DistributedGeohashClustering.encode(48.8566, 2.3522, 6);
        assert.ok(hash.startsWith("u09t"));
    });

    it("calculates Haversine distance and queries spatial radius correctly", () => {
        const cluster = new DistributedGeohashClustering();

        // Madrid center (40.4168, -3.7038)
        const madrid = { latitude: 40.4168, longitude: -3.7038 };
        // Toledo (~67 km away from Madrid)
        const toledo = { latitude: 39.8628, longitude: -4.0273 };
        // Barcelona (~505 km away from Madrid)
        const barcelona = { latitude: 41.3851, longitude: 2.1734 };

        cluster.insert({ id: "loc_toledo", coordinate: toledo, data: { name: "Toledo" } });
        cluster.insert({ id: "loc_barcelona", coordinate: barcelona, data: { name: "Barcelona" } });

        // Query 100km radius around Madrid -> Should find Toledo but not Barcelona
        const nearMadrid = cluster.queryRadius(madrid, 100);
        assert.equal(nearMadrid.length, 1);
        assert.equal(nearMadrid[0].point.id, "loc_toledo");
        assert.ok(nearMadrid[0].distanceKm > 60 && nearMadrid[0].distanceKm < 80);

        // Query 600km radius around Madrid -> Should find both
        const broad = cluster.queryRadius(madrid, 600);
        assert.equal(broad.length, 2);
    });

    it("defensively handles invalid coordinates and empty searches", () => {
        const cluster = new DistributedGeohashClustering();

        assert.equal(DistributedGeohashClustering.encode(NaN, 0), "");
        assert.deepEqual(cluster.queryRadius(null as any, 10), []);

        cluster.insert({ id: "bad", coordinate: { latitude: NaN, longitude: 0 } });
        assert.equal(cluster.size, 0);
    });
});