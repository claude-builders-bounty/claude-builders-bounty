import importlib.util
import sys
from pathlib import Path


HOOK_PATH = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "block_destructive_bash.py"
SPEC = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
HOOK = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = HOOK
SPEC.loader.exec_module(HOOK)


def test_blocks_rm_rf():
    assert HOOK.find_block_reason("rm -rf /tmp/build")


def test_blocks_force_push():
    assert HOOK.find_block_reason("git push --force origin main")


def test_blocks_drop_table():
    assert HOOK.find_block_reason("psql -c 'DROP TABLE users;'")


def test_blocks_delete_without_where():
    assert HOOK.find_block_reason("mysql -e 'DELETE FROM users;'")


def test_allows_delete_with_where():
    assert HOOK.find_block_reason("mysql -e 'DELETE FROM users WHERE id = 1;'") is None


def test_allows_safe_command():
    assert HOOK.find_block_reason("npm test") is None
