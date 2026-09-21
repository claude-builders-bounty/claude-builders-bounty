import { db } from "@/lib/db";

export type Project = {
  id: number;
  ownerId: number;
  name: string;
  createdAt: string;
};

type ProjectRow = {
  id: number;
  owner_id: number;
  name: string;
  created_at: string;
};

export function listProjectsByOwner(ownerId: number): Project[] {
  const rows = db
    .prepare("SELECT id, owner_id, name, created_at FROM projects WHERE owner_id = ? ORDER BY id")
    .all(ownerId) as ProjectRow[];
  return rows.map((row) => ({
    id: row.id,
    ownerId: row.owner_id,
    name: row.name,
    createdAt: row.created_at,
  }));
}
