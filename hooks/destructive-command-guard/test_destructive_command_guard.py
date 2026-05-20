#!/usr/bin/env python3
"""Unit tests for destructive_command_guard.py."""

from destructive_command_guard import classify_command


def test_blocks_rm_rf_variants() -> None:
    assert classify_command("rm -rf build") == "recursive forced removal"
    assert classify_command("rm -fr build") == "recursive forced removal"
    assert classify_command("rm -r -f build") == "recursive forced removal"


def test_blocks_force_push_variants() -> None:
    assert classify_command("git push --force origin main") == "force push"
    assert classify_command("git push -f origin main") == "force push"
    assert classify_command("git push --force-with-lease origin main") == "force push"


def test_blocks_destructive_sql() -> None:
    assert classify_command("psql -c 'DROP TABLE users'") == "DROP TABLE statement"
    assert classify_command("sqlite3 app.db 'TRUNCATE sessions'") == "TRUNCATE statement"
    assert classify_command("mysql -e 'DELETE FROM users'") == "DELETE FROM statement without WHERE"


def test_allows_normal_commands() -> None:
    assert classify_command("rm build.log") is None
    assert classify_command("git push origin main") is None
    assert classify_command("sqlite3 app.db 'DELETE FROM users WHERE id = 1'") is None
    assert classify_command("npm test") is None


if __name__ == "__main__":
    test_blocks_rm_rf_variants()
    test_blocks_force_push_variants()
    test_blocks_destructive_sql()
    test_allows_normal_commands()
    print("ok")

