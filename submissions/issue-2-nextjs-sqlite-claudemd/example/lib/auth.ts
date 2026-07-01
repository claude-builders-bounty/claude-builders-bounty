import { cookies } from "next/headers";
import { db } from "@/lib/db";
import type { User } from "@/lib/repos/users";
import { getUserById } from "@/lib/repos/users";

// Cookie session helpers. A stateful session table (see schema.sql) keeps this
// trivial and avoids JWT footguns. Reference implementation — wire the cookie
// name / session issuance to your auth flow.

export async function getSession(): Promise<User | null> {
  const sid = (await cookies()).get("session")?.value;
  if (!sid) return null;
  const row = db
    .prepare("SELECT user_id, expires_at FROM sessions WHERE id = ?")
    .get(sid) as { user_id: string; expires_at: number } | undefined;
  if (!row || row.expires_at < Date.now()) return null;
  return getUserById(row.user_id);
}

export async function requireUser(): Promise<User> {
  const user = await getSession();
  if (!user) throw new Error("UNAUTHENTICATED");
  return user;
}
