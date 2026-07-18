import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { db, runMigrations, setMigrations } from './db';

const MIGRATIONS_DIR = join(process.cwd(), 'src', 'migrations');

// Lexical order === apply order. Never renumber a closed migration.
const files = readdirSync(MIGRATIONS_DIR)
  .filter((f) => f.endsWith('.sql'))
  .sort();

const migrations = files.map((name) => ({
  name,
  sql: readFileSync(join(MIGRATIONS_DIR, name), 'utf8'),
}));

setMigrations(migrations);
runMigrations();

console.log(`Applied ${migrations.length} migration(s).`);
db.close();
