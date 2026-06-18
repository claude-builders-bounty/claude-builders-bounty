import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).with_name("destructive_command_guard.py")


def run(cmd):
      data = json.dumps({"tool_input": {"command": cmd}, "cwd": "/tmp/demo"})
      return subprocess.run([sys.executable, str(HOOK)], input=data, text=True, capture_output=True)


def test_blocks_required_commands():
      assert run("rm -rf /tmp/x").returncode != 0
      assert run('psql -c "DROP TABLE users"').returncode != 0
      assert run("git push --force origin main").returncode != 0
      assert run('psql -c "TRUNCATE logs"').returncode != 0
      assert run('psql -c "DELETE FROM users"').returncode != 0


def test_allows_safe_commands():
      assert run('psql -c "DELETE FROM users WHERE id = 1"').returncode == 0
      assert run("git push origin main").returncode == 0
      assert run("echo ok").returncode == 0
  
