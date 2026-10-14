import { db } from "../../db";

export type Project = {
  id: string;
  user_id: string;
  name: string;
  created_at: string;
  updated_at: string;
};

export function findProjectById(id: string): Project | undefined {
  return db.prepare("SELECT * FROM projects WHERE id = ?").get(id) as Project | undefined;
}

export function listProjectsByUserId(userId: string): Project[] {
  return db.prepare("SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC").all(userId) as Project[];
}

export function createProject(id: string, userId: string, name: string): Project {
  db.prepare("INSERT INTO projects (id, user_id, name) VALUES (?, ?, ?)").run(id, userId, name);
  return findProjectById(id)!;
}
