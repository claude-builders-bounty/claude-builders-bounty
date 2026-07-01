"use server";

import { revalidatePath } from "next/cache";
import { requireUser } from "@/lib/auth";
import { createUserInput } from "@/lib/validation/user";
import { insertUser } from "@/lib/repos/users";

// Canonical Server Action shape: requireUser → zod.parse → repo → revalidate.
// Client components call this directly; no /api route, no client-side fetch.
export async function createUser(formData: FormData) {
  await requireUser();
  const input = createUserInput.parse({
    email: formData.get("email"),
    name: formData.get("name") || undefined,
  });
  const user = insertUser(input);
  revalidatePath("/users");
  return user;
}
