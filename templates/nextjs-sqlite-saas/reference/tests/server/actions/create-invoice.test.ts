import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { revalidatePath } from "next/cache";
import { actionCreateInvoice } from "@/server/actions/create-invoice";
import * as auth from "@/lib/auth";
import { resetDbForTests } from "@/lib/db";
import { applyAllMigrations, seedOrganization } from "../../helpers/db";

vi.mock("@/lib/auth");
vi.mock("next/cache", () => ({
  revalidatePath: vi.fn(),
}));

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

  it("revalidates the org invoice list path on success", async () => {
    await actionCreateInvoice({ orgSlug: "acme", amountCents: 1000 });
    expect(vi.mocked(revalidatePath)).toHaveBeenCalledWith("/acme/invoices");
  });

  it("returns error when org membership check fails", async () => {
    vi.mocked(auth.requireOrgMember).mockRejectedValue(new Error("Forbidden"));
    const result = await actionCreateInvoice({ orgSlug: "acme", amountCents: 1000 });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toBe("Failed to create invoice");
  });
});
