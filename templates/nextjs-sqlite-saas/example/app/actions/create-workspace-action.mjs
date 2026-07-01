"use server";

import { createWorkspace } from "../../db/queries/workspaces.mjs";
import { validateCreateWorkspace } from "../../lib/validation/workspaces.mjs";

export async function createWorkspaceAction({ db, currentUser, formData }) {
  if (!currentUser) {
    return { ok: false, formError: "Sign in before creating a workspace." };
  }

  const parsed = validateCreateWorkspace({
    name: formData.get("name"),
    slug: formData.get("slug"),
  });

  if (!parsed.ok) {
    return { ok: false, fieldErrors: parsed.errors };
  }

  const workspace = createWorkspace(db, {
    id: crypto.randomUUID(),
    ownerId: currentUser.id,
    ...parsed.data,
  });

  return { ok: true, workspace };
}
