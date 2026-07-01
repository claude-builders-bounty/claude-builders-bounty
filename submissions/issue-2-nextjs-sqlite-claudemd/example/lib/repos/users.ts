import { randomUUID } from "node:crypto";
import { db } from "@/lib/db";
import type { CreateUserInput } from "@/lib/validation/user";

// One file per table. Repos return domain types (camelCase), never raw rows,
// and always use parameterized SQL (? placeholders) — never string interpolation.

export type User = {
  id: string;
  email: string;
  name: string | null;
  isActive: boolean;
  createdAt: number;
  updatedAt: number;
};

type UserRow = {
  id: string;
  email: string;
  name: string | null;
  is_active: number;
  created_at: number;
  updated_at: number;
};

const toUser = (r: UserRow): User => ({
  id: r.id,
  email: r.email,
  name: r.name,
  isActive: r.is_active === 1,
  createdAt: r.created_at,
  updatedAt: r.updated_at,
});

export function getUserById(id: string): User | null {
  const row = db.prepare("SELECT * FROM users WHERE id = ?").get(id) as UserRow | undefined;
  return row ? toUser(row) : null;
}

export function getUserByEmail(email: string): User | null {
  const row = db.prepare("SELECT * FROM users WHERE email = ?").get(email) as UserRow | undefined;
  return row ? toUser(row) : null;
}

export function insertUser(input: CreateUserInput): User {
  const id = randomUUID();
  db.prepare("INSERT INTO users (id, email, name) VALUES (?, ?, ?)").run(
    id,
    input.email,
    input.name ?? null,
  );
  return getUserById(id)!;
}
