import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { listInvoices } from "@/db/queries/invoices";
import { resetDbForTests } from "@/lib/db";
import { actionCreateInvoice } from "@/server/actions/create-invoice";
import { actionVoidInvoice } from "@/server/actions/void-invoice";
import { applyAllMigrations, seedOrganization } from "../helpers/db";

describe("invoice lifecycle (integration)", () => {
  beforeEach(() => {
    applyAllMigrations();
    seedOrganization("org-1", "acme");
  });

  afterEach(() => {
    resetDbForTests();
  });

  it("creates and voids an invoice end-to-end through server actions", async () => {
    const createResult = await actionCreateInvoice({ orgSlug: "acme", amountCents: 5000 });
    expect(createResult.ok).toBe(true);
    if (!createResult.ok) return;

    const invoices = listInvoices("org-1");
    expect(invoices).toHaveLength(1);
    expect(invoices[0]?.amountCents).toBe(5000);

    const voidResult = await actionVoidInvoice({
      orgSlug: "acme",
      invoiceId: createResult.invoice.id,
    });
    expect(voidResult.ok).toBe(true);

    const [voided] = listInvoices("org-1");
    expect(voided?.status).toBe("void");
  });

  it("rejects voiding an invoice from another org", async () => {
    seedOrganization("org-other", "other");
    const createResult = await actionCreateInvoice({ orgSlug: "other", amountCents: 1000 });
    expect(createResult.ok).toBe(true);
    if (!createResult.ok) return;

    const voidResult = await actionVoidInvoice({
      orgSlug: "acme",
      invoiceId: createResult.invoice.id,
    });
    expect(voidResult.ok).toBe(false);
  });
});
