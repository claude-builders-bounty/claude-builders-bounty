"""Fake local fixture data only; never accepts a remote or production DB path."""
import os
from pathlib import Path
import sqlite3

if __name__ == '__main__':
    path = Path(os.environ.get('DATABASE_PATH', '')).resolve()
    if path != (Path(__file__).parent / 'local.db').resolve():
        raise SystemExit('Seed allowed only with DATABASE_PATH=local.db in fixture directory.')
    with sqlite3.connect(path) as db:
        db.execute('PRAGMA foreign_keys = ON')
        db.execute('INSERT OR IGNORE INTO organizations VALUES (?)', ('demo-organization',))
        db.execute('INSERT OR IGNORE INTO projects VALUES (?, ?, ?)',
                   ('demo-project', 'demo-organization', 'Example project'))
    print('Local fixture seeded with fake data.')
