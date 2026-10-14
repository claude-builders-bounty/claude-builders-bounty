import json, os, subprocess, sys, tempfile, unittest

HOOK = os.path.join(os.path.dirname(__file__), "..", "hooks", "block-destructive.py")


def run(cmd, home, tool="Bash"):
    env = dict(os.environ, HOME=home)
    p = subprocess.run([sys.executable, HOOK], env=env, capture_output=True, text=True,
                       input=json.dumps({"tool_name": tool, "cwd": "/proj",
                                         "tool_input": {"command": cmd}}))
    return p


class T(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()

    def test_blocked(self):
        for c in ["rm -rf /", "rm -fr x", "rm -r -f x", "sudo rm --recursive --force x",
                  "ls && rm -rf build", "git push --force", "git push -f origin main",
                  "git push origin main --force", "psql -c 'DROP TABLE users'",
                  "mysql -e 'drop table x;'", "TRUNCATE TABLE users", "truncate users",
                  "psql -c 'DELETE FROM users'", "sqlite3 d 'DELETE FROM t;'"]:
            p = run(c, self.home)
            self.assertEqual(p.returncode, 2, c)
            self.assertIn("BLOCKED", p.stderr)

    def test_allowed(self):
        for c in ["ls -la", "rm file.txt", "rm -r dir", "rm -f file", "git push",
                  "git push --force-with-lease", "git status",
                  "DELETE FROM users WHERE id=1", "echo hello", "npm run build",
                  "grep -rf pattern ."]:
            self.assertEqual(run(c, self.home).returncode, 0, c)
        self.assertEqual(run("rm -rf /", self.home, tool="Read").returncode, 0)

    def test_log(self):
        run("rm -rf /tmp/x", self.home)
        log = open(os.path.join(self.home, ".claude/hooks/blocked.log")).read()
        self.assertIn("rm -rf /tmp/x", log)
        self.assertIn("project=/proj", log)
        self.assertRegex(log, r"^\d{4}-\d\d-\d\dT")


if __name__ == "__main__":
    unittest.main()
