"use client";

import { useActionState } from "react";
import { actionCreateInvoice } from "@/server/actions/create-invoice";

/** Client form wired to `actionCreateInvoice` via `useActionState` — see CLAUDE.md Component Patterns. */
export function CreateInvoiceForm({ orgSlug }: { orgSlug: string }) {
  const [state, formAction, pending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      const amountCents = Number(formData.get("amountCents"));
      return actionCreateInvoice({ orgSlug, amountCents });
    },
    null,
  );

  return (
    <form action={formAction}>
      <input name="amountCents" type="number" required />
      <button disabled={pending}>Create</button>
      {state?.ok === false && <p role="alert">{state.error}</p>}
      {state?.ok && <p>Invoice created</p>}
    </form>
  );
}
