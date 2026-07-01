import { db } from "@/lib/db";
import { createUser } from "./actions";

// Server Component: fetches via the DB, renders, passes plain data down.
// Thin route — no business logic here; it lives in lib/.
export default function UsersPage() {
  const users = db
    .prepare("SELECT id, email, name FROM users ORDER BY created_at DESC LIMIT 50")
    .all() as { id: string; email: string; name: string | null }[];

  return (
    <main className="mx-auto max-w-lg p-6">
      <h1 className="text-xl font-semibold">Users</h1>

      <form action={createUser} className="mt-4 flex gap-2">
        <input name="email" type="email" placeholder="email" required className="border px-2" />
        <input name="name" placeholder="name" className="border px-2" />
        <button type="submit" className="border px-3">Add</button>
      </form>

      <ul className="mt-4 space-y-1">
        {users.map((u) => (
          <li key={u.id}>{u.name ?? "—"} · {u.email}</li>
        ))}
      </ul>
    </main>
  );
}
