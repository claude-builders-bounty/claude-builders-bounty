"""Regression tests found by independent review; input is never executed."""
import importlib.util
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location("guard_regression", Path(__file__).resolve().parents[1] / "guard.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class ReviewRegressions(unittest.TestCase):
    def test_leading_file_descriptor_redirection(self):
        for command in ("2>/dev/null rm -rf /tmp/demo", "2>errors env X=1 git push -f"):
            with self.subTest(command=command):
                self.assertIsNotNone(guard.inspect(command))

    def test_mysql_hash_comment_is_not_where(self):
        self.assertIsNotNone(guard.inspect("mysql -e 'DELETE FROM users # WHERE id=1'"))

    def test_mysql_executable_comment(self):
        for command in ("mysql -e '/*! DELETE FROM users */;'", "mysql -e '/*!50000 DROP TABLE users */;'",
                        "mariadb -e '/*M!100100 TRUNCATE users */;'"):
            with self.subTest(command=command):
                self.assertIsNotNone(guard.inspect(command))

    def test_nested_sql_comment_is_not_where(self):
        self.assertIsNotNone(guard.inspect("psql -c 'DELETE FROM users /* outer /* inner */ WHERE x */;'"))

    def test_printf_literal_pipeline(self):
        for command in ("printf '%s\\n' 'TRUNCATE TABLE users;' | psql",
                        "printf '%s ' rm -rf /tmp/demo | bash"):
            with self.subTest(command=command):
                self.assertIsNotNone(guard.inspect(command))

    def test_printf_safe_literal_pipeline(self):
        self.assertIsNone(guard.inspect("printf '%s\\n' 'SELECT 1;' | psql"))

    def test_command_lookup_does_not_execute(self):
        for command in ("command -v rm -rf /tmp/demo", "command -pV git push -f"):
            self.assertIsNone(guard.inspect(command))

    def test_escaped_heredoc_delimiter_does_not_expand(self):
        self.assertIsNone(guard.inspect("cat <<\\EOF\n$(rm -rf /tmp/demo)\nEOF\n"))


if __name__ == "__main__":
    unittest.main()
