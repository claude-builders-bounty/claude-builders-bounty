import { randomUUID } from "node:crypto";
import { getDb } from "@/lib/db";

export type Invoice = {
  id: string;
  orgId: string;
  amountCents: number;
  status: string;
};

/** Lists invoices for one org. All dynamic values bind via `?` placeholders — never interpolate SQL. */
export function listInvoices(orgId: string): Invoice[] {
  const db = getDb();
  const rows = db
    .prepare(
      `SELECT id, org_id, amount_cents, status
       FROM invoices
       WHERE org_id = ? AND deleted_at IS NULL
       ORDER BY created_at DESC, id DESC
       LIMIT 100`,
    )
    .all(orgId) as Array<{
      id: string;
      org_id: string;
      amount_cents: number;
      status: string;
    }>;

  return rows.map((row) => ({
    id: row.id,
    orgId: row.org_id,
    amountCents: row.amount_cents,
    status: row.status,
  }));
}

/** Inserts a draft invoice scoped to org_id. Uses parameterized INSERT — no string concatenation. */
export function createInvoice(input: {
  orgId: string;
  amountCents: number;
  createdBy: string;
}): Invoice {
  const db = getDb();
  const id = randomUUID();
  db.prepare(
    `INSERT INTO invoices (id, org_id, amount_cents, status)
     VALUES (?, ?, ?, 'draft')`,
  ).run(id, input.orgId, input.amountCents);

  return { id, orgId: input.orgId, amountCents: input.amountCents, status: "draft" };
}

/** Voids an invoice within org scope. Both id and org_id bind as `?` parameters to prevent SQL injection. */
export function voidInvoice(input: { orgId: string; invoiceId: string }): void {
  const db = getDb();
  const result = db
    .prepare(
      `UPDATE invoices
       SET status = 'void',
           updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
       WHERE id = ? AND org_id = ? AND deleted_at IS NULL`,
    )
    .run(input.invoiceId, input.orgId);

  if (result.changes === 0) {
    throw new Error("Invoice not found");
  }
}
