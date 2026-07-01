import { listUsers } from "../../../db/queries/users.mjs";

type QueryDb = {
  prepare(sql: string): {
    all(): Array<{ id: string; email: string }>;
  };
};

type DashboardPageProps = {
  db: QueryDb;
};

export default async function DashboardPage({ db }: DashboardPageProps) {
  const users = listUsers(db);

  return (
    <main>
      <h1>Dashboard</h1>
      <ul>
        {users.map((user) => (
          <li key={user.id}>{user.email}</li>
        ))}
      </ul>
    </main>
  );
}
