#!/usr/bin/env python3
"""Unit tests for block_destructive_bash.py."""

import importlib.util
import pathlib
import unittest


HOOK_PATH = pathlib.Path(__file__).with_name("block_destructive_bash.py")
SPEC = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
module = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(module)


class DestructiveCommandTests(unittest.TestCase):
    def test_blocks_rm_rf(self):
        self.assertIsNotNone(module.destructive_reason("rm -rf /tmp/cache"))
        self.assertIsNotNone(module.destructive_reason("rm -fr build"))

    def test_blocks_sql_destruction(self):
        self.assertIsNotNone(module.destructive_reason("psql -c 'DROP TABLE users'"))
        self.assertIsNotNone(module.destructive_reason("TRUNCATE TABLE events"))
        self.assertIsNotNone(module.destructive_reason("mysql -e 'DELETE FROM users'"))

    def test_allows_delete_with_where(self):
        self.assertIsNone(module.destructive_reason("mysql -e 'DELETE FROM users WHERE id = 1'"))

    def test_blocks_force_push(self):
        self.assertIsNotNone(module.destructive_reason("git push origin main --force"))
        self.assertIsNotNone(module.destructive_reason("git push -f origin main"))
        self.assertIsNotNone(module.destructive_reason("git push --force-with-lease"))

    def test_allows_normal_commands(self):
        self.assertIsNone(module.destructive_reason("npm test"))
        self.assertIsNone(module.destructive_reason("git push origin main"))
        self.assertIsNone(module.destructive_reason("python manage.py migrate --plan"))


if __name__ == "__main__":
    unittest.main()
