import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { createInvoice, listInvoices, voidInvoice } from "@/db/queries/invoices";
import { resetDbForTests } from "@/lib/db";
import { applyAllMigrations, seedOrganization } from "../../helpers/db";

describe("invoice queries (integration)", () => {
  const orgId = "org-1";
  const orgSlug = "acme";

  beforeEach(() => {
    applyAllMigrations();
    seedOrganization(orgId, orgSlug);
  });

  afterEach(() => {
    resetDbForTests();
  });

  it("lists invoices scoped to org_id", () => {
    seedOrganization("org-other", "other");
    createInvoice({ orgId, amountCents: 1500, createdBy: "user-1" });
    createInvoice({ orgId: "org-other", amountCents: 999, createdBy: "user-2" });

    const invoices = listInvoices(orgId);
    expect(invoices).toHaveLength(1);
    expect(invoices[0]?.amountCents).toBe(1500);
  });

  it("voids an invoice within the org scope", () => {
    const invoice = createInvoice({ orgId, amountCents: 2000, createdBy: "user-1" });
    voidInvoice({ orgId, invoiceId: invoice.id });

    const [voided] = listInvoices(orgId);
    expect(voided?.status).toBe("void");
  });
});
