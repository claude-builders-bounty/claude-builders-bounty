"""Apply immutable SQL files and bookkeeping atomically; stdlib-only runner."""
import hashlib
import os
from pathlib import Path
import sqlite3


def migrate(db: sqlite3.Connection, directory: Path) -> None:
    db.execute('PRAGMA foreign_keys = ON')
    db.execute('PRAGMA busy_timeout = 5000')
    db.execute('CREATE TABLE IF NOT EXISTS schema_migrations '
               '(version TEXT PRIMARY KEY, checksum TEXT NOT NULL)')
    db.commit()
    for path in sorted(directory.glob('[0-9][0-9][0-9][0-9]_*.sql')):
        sql = path.read_text(encoding='utf-8')
        checksum = hashlib.sha256(sql.encode()).hexdigest()
        row = db.execute('SELECT checksum FROM schema_migrations WHERE version = ?',
                         (path.name,)).fetchone()
        if row:
            if row[0] != checksum:
                raise ValueError('Applied migration checksum changed: ' + path.name)
            continue
        try:
            db.executescript('BEGIN IMMEDIATE;\n' + sql)
            db.execute('INSERT INTO schema_migrations VALUES (?, ?)',
                       (path.name, checksum))
            db.commit()
        except BaseException:
            db.rollback()
            raise


if __name__ == '__main__':
    path = os.environ.get('DATABASE_PATH')
    if not path:
        raise SystemExit('Set DATABASE_PATH explicitly before migrating.')
    with sqlite3.connect(path) as connection:
        migrate(connection, Path(__file__).parent / 'migrations')
    print('Migrations applied successfully.')
