"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { requireOrgMember } from "@/lib/auth";
import { createInvoice } from "@/db/queries/invoices";

const schema = z.object({
  orgSlug: z.string().min(1),
  amountCents: z.number().int().positive(),
});

export async function actionCreateInvoice(input: unknown) {
  const parsed = schema.safeParse(input);
  if (!parsed.success) {
    return { ok: false as const, error: "Invalid input" };
  }
  const data = parsed.data;
  try {
    const { orgId, userId } = await requireOrgMember(data.orgSlug);
    const invoice = createInvoice({
      orgId,
      amountCents: data.amountCents,
      createdBy: userId,
    });
    revalidatePath(`/${data.orgSlug}/invoices`);
    return { ok: true as const, invoice };
  } catch {
    return { ok: false as const, error: "Failed to create invoice" };
  }
}
