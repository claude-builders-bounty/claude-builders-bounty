import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import test from 'node:test';
import { createClient } from '@libsql/client';

const hash = (sql) => createHash('sha256').update(sql).digest('hex');
const initial = {
  version: 1,
  sql: `
    CREATE TABLE tenants (id TEXT PRIMARY KEY);
    CREATE TABLE projects (
      tenant_id TEXT NOT NULL REFERENCES tenants(id),
      id TEXT NOT NULL,
      name TEXT NOT NULL,
      PRIMARY KEY (tenant_id, id)
    );
    CREATE TABLE tasks (
      tenant_id TEXT NOT NULL,
      id TEXT NOT NULL,
      project_id TEXT NOT NULL,
      PRIMARY KEY (tenant_id, id),
      FOREIGN KEY (tenant_id, project_id) REFERENCES projects(tenant_id, id)
    );
    INSERT INTO tenants VALUES ('a'), ('b');
    INSERT INTO projects VALUES ('a', 'p1', 'A; project');
  `,
};
const upgrade = {
  version: 2,
  sql: `ALTER TABLE projects ADD COLUMN archived INTEGER NOT NULL DEFAULT 0
    CHECK (archived IN (0, 1));`,
};

// Test-only runner for trusted SQL constants, not a production migration CLI.
async function migrate(db, migrations) {
  for (const [index, migration] of migrations.entries()) {
    assert(Number.isSafeInteger(migration.version) && migration.version > 0);
    assert(index === 0 || migrations[index - 1].version < migration.version,
      'duplicate or out-of-order migration');
  }
  const tx = await db.transaction('write');
  try {
    await tx.execute(`CREATE TABLE IF NOT EXISTS schema_migrations (
      version INTEGER PRIMARY KEY, checksum TEXT NOT NULL, applied_at INTEGER NOT NULL
    )`);
    const { rows } = await tx.execute('SELECT version, checksum FROM schema_migrations ORDER BY version');
    for (const [index, applied] of rows.entries()) {
      const source = migrations[index];
      assert(source && source.version === Number(applied.version), 'missing or reordered applied migration');
      assert.equal(hash(source.sql), applied.checksum, 'migration checksum mismatch');
    }
    for (const migration of migrations.slice(rows.length)) {
      await tx.executeMultiple(migration.sql);
      await tx.execute({
        sql: 'INSERT INTO schema_migrations VALUES (?, ?, ?)',
        args: [migration.version, hash(migration.sql), Date.now()],
      });
    }
    await tx.commit();
  } finally {
    // executeMultiple does not roll back on failure; close rolls back uncommitted work.
    tx.close();
  }
}

async function withDatabase(run) {
  const db = createClient({ url: 'file::memory:' });
  try {
    await db.execute('PRAGMA foreign_keys = ON');
    assert.equal((await db.execute('PRAGMA foreign_keys')).rows[0].foreign_keys, 1);
    await run(db);
  } finally {
    db.close();
  }
}

test('fresh database, repeated run, and semicolon inside SQL string', async () => {
  await withDatabase(async (db) => {
    await migrate(db, [initial]);
    await migrate(db, [initial]);
    assert.equal((await db.execute('SELECT count(*) AS n FROM schema_migrations')).rows[0].n, 1);
    assert.equal((await db.execute('SELECT name FROM projects')).rows[0].name, 'A; project');
  });
});

test('upgrade preserves data and initializes new constrained column', async () => {
  await withDatabase(async (db) => {
    await migrate(db, [initial]);
    await migrate(db, [initial, upgrade]);
    const { rows } = await db.execute('SELECT name, archived FROM projects');
    assert.equal(rows[0].name, 'A; project');
    assert.equal(rows[0].archived, 0);
    await assert.rejects(db.execute('UPDATE projects SET archived = 2'));
  });
});

test('checksum drift and missing applied history fail closed', async () => {
  await withDatabase(async (db) => {
    await migrate(db, [initial]);
    await assert.rejects(migrate(db, [{ ...initial, sql: initial.sql + '\n' }]), /checksum/);
    await assert.rejects(migrate(db, []), /missing/);
    assert.equal((await db.execute('SELECT count(*) AS n FROM projects')).rows[0].n, 1);
  });
});

test('duplicate and out-of-order versions are rejected', async () => {
  await withDatabase(async (db) => {
    await assert.rejects(migrate(db, [initial, initial]), /duplicate/);
    await assert.rejects(migrate(db, [upgrade, initial]), /out-of-order/);
  });
});

test('malformed later SQL rolls back schema, data, and ledger together', async () => {
  await withDatabase(async (db) => {
    await migrate(db, [initial]);
    await assert.rejects(migrate(db, [initial, {
      version: 2,
      sql: `CREATE TABLE partial (id TEXT); INSERT INTO partial VALUES ('not committed');
        THIS IS NOT VALID SQL;`,
    }]));
    assert.equal((await db.execute("SELECT count(*) AS n FROM sqlite_master WHERE name = 'partial'")).rows[0].n, 0);
    assert.equal((await db.execute('SELECT count(*) AS n FROM schema_migrations')).rows[0].n, 1);
    await migrate(db, [initial, upgrade]);
  });
});

test('composite foreign key rejects cross-tenant reference and accepts same-tenant reference', async () => {
  await withDatabase(async (db) => {
    await migrate(db, [initial]);
    await assert.rejects(db.execute({
      sql: 'INSERT INTO tasks VALUES (?, ?, ?)', args: ['b', 't1', 'p1'],
    }), /FOREIGN KEY/);
    await db.execute({ sql: 'INSERT INTO tasks VALUES (?, ?, ?)', args: ['a', 't1', 'p1'] });
    assert.equal((await db.execute('SELECT count(*) AS n FROM tasks')).rows[0].n, 1);
  });
});

test('tenant-bound reads and writes do not expose or alter another tenant row', async () => {
  await withDatabase(async (db) => {
    await migrate(db, [initial]);
    const result = await db.execute({
      sql: 'SELECT name FROM projects WHERE tenant_id = ? AND id = ?', args: ['b', 'p1'],
    });
    assert.equal(result.rows.length, 0);
    const write = await db.execute({
      sql: 'UPDATE projects SET name = ? WHERE tenant_id = ? AND id = ?', args: ['changed', 'b', 'p1'],
    });
    assert.equal(write.rowsAffected, 0);
    assert.equal((await db.execute('SELECT name FROM projects')).rows[0].name, 'A; project');
  });
});

test('bound malicious-looking input remains data', async () => {
  await withDatabase(async (db) => {
    await migrate(db, [initial]);
    const name = "x'); DROP TABLE tenants; --";
    await db.execute({ sql: 'INSERT INTO projects VALUES (?, ?, ?)', args: ['b', 'p2', name] });
    assert.equal((await db.execute({ sql: 'SELECT name FROM projects WHERE tenant_id = ? AND id = ?', args: ['b', 'p2'] })).rows[0].name, name);
    assert.equal((await db.execute('SELECT count(*) AS n FROM tenants')).rows[0].n, 2);
  });
});
