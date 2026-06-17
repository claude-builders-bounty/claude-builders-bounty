import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { actionCreateInvoice } from "@/server/actions/create-invoice";
import * as auth from "@/lib/auth";
import { resetDbForTests } from "@/lib/db";
import { applyAllMigrations, seedOrganization } from "../../helpers/db";

vi.mock("@/lib/auth");

describe("actionCreateInvoice", () => {
  beforeEach(() => {
    applyAllMigrations();
    seedOrganization("org-1", "acme");
    vi.mocked(auth.requireOrgMember).mockResolvedValue({
      orgId: "org-1",
      userId: "user-1",
    });
  });

  afterEach(() => {
    resetDbForTests();
    vi.resetAllMocks();
  });

  it("returns structured error for invalid input", async () => {
    const result = await actionCreateInvoice({ orgSlug: "", amountCents: -1 });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toBeDefined();
  });

  it("returns ok with invoice on success", async () => {
    const result = await actionCreateInvoice({ orgSlug: "acme", amountCents: 1000 });
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.invoice).toBeDefined();
  });
});
