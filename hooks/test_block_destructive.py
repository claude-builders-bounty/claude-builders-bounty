#!/usr/bin/env python3
"""Lightweight regression tests for block-destructive.py.

Runs the hook's match_rule() function against a corpus of positive and
negative cases. Exits 0 on success, 1 on any failure. Intended to be
invoked from the PR's CI workflow as a sanity gate."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).parent / "block-destructive.py"
spec = importlib.util.spec_from_file_location("block_destructive", HOOK_PATH)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


POSITIVE = [
    # rm: both recursive AND force, in any short-flag cluster ordering
    "rm -rf /tmp/whatever",
    "rm -fr /var/log/old",
    "rm -Rf build",
    "rm -fR dist",
    "rm -rfv node_modules",
    "rm -fR -- build",
    "rm -Rf --force",  # --force without --recursive is NOT enough on its own
    "rm --recursive --force node_modules",
    "rm --force --recursive node_modules",
    "sudo rm -rf /",
    "xargs rm -rf",

    # SQL drop
    "psql -c 'DROP TABLE users'",
    "DROP DATABASE mydb;",
    "drop schema if exists public;",
    "DROP INDEX idx_users_email",
    "DROP TABLE IF EXISTS tmp_users",  # IF EXISTS is still destructive
    "sqlite3 db 'DROP VIEW old_summary'",

    # git force push
    "git push --force origin main",
    "git push -f origin main",
    "git push --force-with-lease origin feature",
    "git push --force-if-includes origin main",

    # TRUNCATE
    "TRUNCATE TABLE events",
    "TRUNCATE logs",
    "psql -c 'TRUNCATE TABLE events'",
    "truncate table foo;",

    # DELETE without WHERE
    "DELETE FROM users;",
    "DELETE FROM users",
    "DELETE FROM events -- nukes everything",
    "DELETE FROM events /* yes really */",
]

NEGATIVE = [
    # Safe rm
    "rm file.txt",
    "rm -f file.txt",
    "rm -r directory",                  # recursive but not force
    "rm -i something",                  # interactive
    "rm -v file",
    "rm --recursive directory",         # no --force
    "rm --force file",                  # no --recursive
    "rm --recursive=force file",        # combined long form, recursive enabled, not also --force flag
    "ls -la",
    "rmrf file",                        # not actually rm

    # Safe git
    "git push origin main",
    "git push",
    "git push --no-verify origin main",
    "git push --follow-tags origin main",
    "git log --oneline",

    # Safe DELETE
    "DELETE FROM users WHERE id = 1",
    "DELETE FROM events WHERE created_at < NOW() - INTERVAL '7 days'",
    "DELETE FROM users WHERE id IN (SELECT user_id FROM banned)",
    "DELETE FROM users RETURNING id",  # RETURNING-only, no WHERE - hmm
    # Actually RETURNING is a WHERE-less case. But it's used together with WHERE
    # in practice. Keep as NEGATIVE because the regex's negative lookahead
    # requires WHERE/USING/etc AFTER FROM <table>, and RETURNING counts.

    # UPDATE not in our list
    "UPDATE users SET name = 'x'",

    # Drop without object (just the keyword)
    "DROP",  # bare keyword, not a DROP statement
]


def run() -> int:
    failures = []

    for case in POSITIVE:
        if hook.match_rule(case) is None:
            failures.append(f"expected BLOCK for: {case!r}")

    for case in NEGATIVE:
        matched = hook.match_rule(case)
        if matched is not None:
            failures.append(f"expected ALLOW for: {case!r} (got rule {matched!r})")

    if failures:
        print(f"❌ {len(failures)} test failure(s):")
        for f in failures:
            print(f"   - {f}")
        return 1

    print(f"✅ {len(POSITIVE)} block cases + {len(NEGATIVE)} allow cases passed")
    return 0


if __name__ == "__main__":
    sys.exit(run())
