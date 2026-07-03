import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { revalidatePath } from "next/cache";
import { actionVoidInvoice } from "@/server/actions/void-invoice";
import { createInvoice } from "@/db/queries/invoices";
import * as auth from "@/lib/auth";
import { resetDbForTests } from "@/lib/db";
import { applyAllMigrations, seedOrganization } from "../../helpers/db";

vi.mock("@/lib/auth");
vi.mock("next/cache", () => ({
  revalidatePath: vi.fn(),
}));

describe("actionVoidInvoice", () => {
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
    const result = await actionVoidInvoice({ orgSlug: "", invoiceId: "" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toBeDefined();
  });

  it("voids an invoice for the resolved org", async () => {
    const invoice = createInvoice({ orgId: "org-1", amountCents: 500, createdBy: "user-1" });
    const result = await actionVoidInvoice({ orgSlug: "acme", invoiceId: invoice.id });
    expect(result.ok).toBe(true);
  });

  it("revalidates the org invoice list path on success", async () => {
    const invoice = createInvoice({ orgId: "org-1", amountCents: 500, createdBy: "user-1" });
    await actionVoidInvoice({ orgSlug: "acme", invoiceId: invoice.id });
    expect(vi.mocked(revalidatePath)).toHaveBeenCalledWith("/acme/invoices");
  });

  it("returns error when org membership check fails", async () => {
    vi.mocked(auth.requireOrgMember).mockRejectedValue(new Error("Forbidden"));
    const invoice = createInvoice({ orgId: "org-1", amountCents: 500, createdBy: "user-1" });
    const result = await actionVoidInvoice({ orgSlug: "acme", invoiceId: invoice.id });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toBe("Failed to void invoice");
  });
});
