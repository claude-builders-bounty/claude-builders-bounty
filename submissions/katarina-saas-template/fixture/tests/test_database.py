import importlib.util
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('migration_runner', ROOT / 'migrate.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class DatabaseContract(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.tmp = tempfile.TemporaryDirectory()
        self.migrations = Path(self.tmp.name)
        shutil.copy(ROOT / 'migrations/0001_initial.sql', self.migrations)
        runner.migrate(self.db, self.migrations)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_repeat_run_is_idempotent(self):
        runner.migrate(self.db, self.migrations)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM schema_migrations').fetchone()[0], 1)

    def test_applied_migration_cannot_be_rewritten(self):
        path = self.migrations / '0001_initial.sql'
        path.write_text(path.read_text() + '\n-- edited\n')
        with self.assertRaisesRegex(ValueError, 'checksum changed'):
            runner.migrate(self.db, self.migrations)

    def test_bad_migration_rolls_back_schema_and_ledger(self):
        (self.migrations / '0002_bad.sql').write_text(
            'CREATE TABLE transient (id TEXT);\nINVALID SQL;')
        with self.assertRaises(sqlite3.OperationalError):
            runner.migrate(self.db, self.migrations)
        self.assertIsNone(self.db.execute(
            "SELECT name FROM sqlite_master WHERE name='transient'").fetchone())
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM schema_migrations').fetchone()[0], 1)

    def test_upgrade_keeps_existing_records(self):
        self.db.execute('INSERT INTO organizations VALUES (?)', ('a',))
        self.db.commit()
        (self.migrations / '0002_upgrade.sql').write_text(
            "ALTER TABLE organizations ADD COLUMN name TEXT NOT NULL DEFAULT '';\n")
        runner.migrate(self.db, self.migrations)
        self.assertEqual(self.db.execute('SELECT id, name FROM organizations').fetchone(), ('a', ''))

    def test_composite_foreign_key_rejects_wrong_tenant(self):
        self.db.executemany('INSERT INTO organizations VALUES (?)', [('a',), ('b',)])
        self.db.execute('INSERT INTO projects VALUES (?, ?, ?)', ('p', 'a', 'Project A'))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('INSERT INTO tasks VALUES (?, ?, ?, ?)', ('t', 'b', 'p', 'wrong'))
        self.db.execute('INSERT INTO tasks VALUES (?, ?, ?, ?)', ('ok', 'a', 'p', 'allowed'))

    def test_bound_query_does_not_accept_tenant_injection(self):
        self.db.execute('INSERT INTO organizations VALUES (?)', ('a',))
        self.db.execute('INSERT INTO projects VALUES (?, ?, ?)', ('p', 'a', 'Project A'))
        rows = self.db.execute('SELECT id FROM projects WHERE organization_id = ?',
                               ("a' OR 1=1 --",)).fetchall()
        self.assertEqual(rows, [])


if __name__ == '__main__':
    unittest.main()
