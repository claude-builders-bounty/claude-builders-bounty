import { listProjectsByOwner } from "@/lib/db/queries/projects";

export function listProjects(ownerId: number) {
  return listProjectsByOwner(ownerId);
}
