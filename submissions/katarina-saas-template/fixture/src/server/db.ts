import 'server-only';
import Database from 'better-sqlite3';

let connection: Database.Database | undefined;
export function db(): Database.Database {
  if (connection) return connection;
  const path = process.env.DATABASE_PATH;
  if (!path) throw new Error('DATABASE_PATH is required');
  connection = new Database(path);
  connection.pragma('foreign_keys = ON');
  connection.pragma('journal_mode = WAL');
  connection.pragma('busy_timeout = 5000');
  return connection;
}

export function listProjects(organizationId: string) {
  return db().prepare(
    'SELECT id, name FROM projects WHERE organization_id = ? ORDER BY name, id LIMIT 50',
  ).all(organizationId) as { id: string; name: string }[];
}
