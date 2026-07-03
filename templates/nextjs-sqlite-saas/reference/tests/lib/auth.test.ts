import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { requireOrgMember } from "@/lib/auth";
import { resetDbForTests } from "@/lib/db";
import { applyAllMigrations, seedOrganization } from "../helpers/db";

describe("requireOrgMember", () => {
  beforeEach(() => {
    applyAllMigrations();
    seedOrganization("org-1", "acme");
  });

  afterEach(() => {
    resetDbForTests();
  });

  it("resolves orgId for a valid slug via parameterized query", async () => {
    const { orgId, userId } = await requireOrgMember("acme");
    expect(orgId).toBe("org-1");
    expect(userId).toBeDefined();
  });

  it("rejects unknown org slug", async () => {
    await expect(requireOrgMember("missing")).rejects.toThrow("Organization not found");
  });

  it("does not resolve SQL injection payloads in org slug", async () => {
    await expect(requireOrgMember("' OR '1'='1")).rejects.toThrow("Organization not found");
  });
});
