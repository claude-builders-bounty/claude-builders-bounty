import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { actionVoidInvoice } from "@/server/actions/void-invoice";
import { createInvoice } from "@/db/queries/invoices";
import * as auth from "@/lib/auth";
import { resetDbForTests } from "@/lib/db";
import { applyAllMigrations, seedOrganization } from "../../helpers/db";

vi.mock("@/lib/auth");

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
});
