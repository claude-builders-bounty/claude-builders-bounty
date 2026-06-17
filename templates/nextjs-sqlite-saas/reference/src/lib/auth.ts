import { getDb } from "@/lib/db";

type OrgRow = { id: string; slug: string };

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
