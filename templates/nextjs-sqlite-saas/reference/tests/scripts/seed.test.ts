import { afterEach, describe, expect, it, vi } from "vitest";
import { applyAllMigrations } from "../helpers/db";
import { assertSeedAllowed, seedDevOrganizations } from "../../scripts/seed";
import { getDb } from "@/lib/db";

describe("scripts/seed", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("blocks production NODE_ENV before seeding", () => {
    const exitSpy = vi.spyOn(process, "exit").mockImplementation((() => {}) as never);
    const prev = process.env.NODE_ENV;
    process.env.NODE_ENV = "production";

    assertSeedAllowed();

    expect(exitSpy).toHaveBeenCalledWith(1);
    process.env.NODE_ENV = prev;
  });

  it("upserts dev organizations idempotently", () => {
    applyAllMigrations();
    const db = getDb();

    seedDevOrganizations(db);
    seedDevOrganizations(db);

    const row = db
      .prepare("SELECT id, slug FROM organizations WHERE id = ?")
      .get("org-dev-1") as { id: string; slug: string };
    expect(row).toEqual({ id: "org-dev-1", slug: "acme" });
    expect(
      (db.prepare("SELECT COUNT(*) AS c FROM organizations").get() as { c: number }).c,
    ).toBe(1);
  });
});
