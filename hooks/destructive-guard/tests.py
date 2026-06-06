"""Unit tests for destructive-guard hook."""
import sys
import os
import json
import io
sys.path.insert(0, os.path.dirname(__file__))
import pytest
from hook import is_blocked, main


@pytest.mark.parametrize("cmd,should_block", [
    # rm -rf variants
    ("rm -rf /",                   True),
    ("rm -rf .",                   True),
    ("rm -rf node_modules",        True),
    ("rm -fr /tmp/foo",            True),
    ("rm -Rf /var/log",            True),
    ("rm -RF /var/log",            True),
    ("rm -r -f /build",            True),
    ("rm -f -r /build",            True),
    ("rm -rdf ./dist",             True),
    # safe rm
    ("rm -f file.txt",             False),
    ("rm -r dir/",                 False),
    ("rm file.txt",                False),
    ("rm -i file.txt",             False),
    # DROP TABLE
    ("DROP TABLE users;",          True),
    ("drop table users;",          True),
    ("DROP TABLE IF EXISTS foo;",  True),
    # TRUNCATE
    ("TRUNCATE orders;",           True),
    ("truncate TABLE logs;",       True),
    # DELETE FROM without WHERE
    ("DELETE FROM users;",         True),
    ("delete from logs;",          True),
    ("DELETE FROM users WHERE id = 1;",    False),
    ("DELETE FROM orders WHERE active=0;", False),
    # git push --force
    ("git push --force origin main",  True),
    ("git push -f origin main",       True),
    ("git push origin main",          False),
    ("git push --force-with-lease",   False),
    # multi-command — still blocked when embedded
    ("echo hello && rm -rf /tmp",  True),
    ("ls; rm -rf .",               True),
    ("sudo rm -rf /var/cache",     True),
    # piped commands — safe side is safe, dangerous side still blocked
    ("cat file.txt | rm -rf -",    True),
    # dd disk overwrite
    ("dd if=/dev/zero of=/dev/sda",   True),
    ("dd if=backup.img of=/dev/sdb1", True),
    ("dd if=/dev/sda of=backup.img",  False),  # reading from disk is safe
    # fork bomb
    (":(){ :|:& };:",              True),
    # normal commands — must not block
    ("ls -la",           False),
    ("echo hello",       False),
    ("find . -name '*.py'", False),
    ("mkdir -p /tmp/build", False),
    ("npm install",      False),
    ("git push --force-with-lease origin main", False),
])
def test_is_blocked(cmd, should_block):
    blocked, reason = is_blocked(cmd)
    assert blocked == should_block, (
        f"Expected {'block' if should_block else 'allow'} for: {cmd!r}\n"
        f"Got blocked={blocked}, reason={reason!r}"
    )


def test_reason_non_empty_when_blocked():
    blocked, reason = is_blocked("rm -rf /tmp")
    assert blocked and reason != ""


def test_reason_empty_when_allowed():
    blocked, reason = is_blocked("ls -la")
    assert not blocked and reason == ""


class TestMain:
    def _run(self, stdin_data: dict | list, capsys, monkeypatch) -> dict:
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(stdin_data)))
        main()
        out = capsys.readouterr().out
        return json.loads(out)

    def test_non_bash_tool_allowed(self, capsys, monkeypatch):
        result = self._run({"tool_name": "Read", "tool_input": {"path": "/etc"}}, capsys, monkeypatch)
        assert result["decision"] == "allow"

    def test_bash_safe_command_allowed(self, capsys, monkeypatch):
        result = self._run({"tool_name": "Bash", "tool_input": {"command": "ls -la"}}, capsys, monkeypatch)
        assert result["decision"] == "allow"

    def test_bash_destructive_blocked(self, capsys, monkeypatch):
        result = self._run({"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}, capsys, monkeypatch)
        assert result["decision"] == "block"
        assert "reason" in result

    def test_non_dict_json_allowed(self, capsys, monkeypatch):
        # Valid JSON that is not a dict — must not crash
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps([1, 2, 3])))
        main()
        out = capsys.readouterr().out
        assert json.loads(out)["decision"] == "allow"

    def test_malformed_json_exits_cleanly(self, monkeypatch):
        monkeypatch.setattr("sys.stdin", io.StringIO("{not valid json"))
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0
