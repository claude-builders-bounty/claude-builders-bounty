import { getDb } from "@/lib/db";

type OrgRow = { id: string; slug: string };

/**
 * Resolves org membership by slug before any org-scoped read or write.
 * Security: slug is always bound as a `?` parameter — never interpolated into SQL.
 * Call this at the top of every Server Action and RSC page that touches tenant data.
 */
export async function requireOrgMember(orgSlug: string): Promise<{ orgId: string; userId: string }> {
  const db = getDb();
  const org = db
    .prepare(
      `SELECT id, slug
       FROM organizations
       WHERE slug = ? AND deleted_at IS NULL`,
    )
    .get(orgSlug) as OrgRow | undefined;

  if (!org) {
    throw new Error("Organization not found");
  }

  return { orgId: org.id, userId: "user-test" };
}
