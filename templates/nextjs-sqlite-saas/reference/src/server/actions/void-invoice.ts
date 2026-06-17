"use server";

import { z } from "zod";
import { requireOrgMember } from "@/lib/auth";
import { voidInvoice } from "@/db/queries/invoices";

const schema = z.object({
  orgSlug: z.string().min(1),
  invoiceId: z.string().min(1),
});

export async function actionVoidInvoice(input: unknown) {
  const parsed = schema.safeParse(input);
  if (!parsed.success) {
    return { ok: false as const, error: "Invalid input" };
  }
  const data = parsed.data;
  try {
    const { orgId } = await requireOrgMember(data.orgSlug);
    voidInvoice({ orgId, invoiceId: data.invoiceId });
    return { ok: true as const };
  } catch {
    return { ok: false as const, error: "Failed to void invoice" };
  }
}
