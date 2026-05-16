"""Tests for bash security pre-tool-use hook"""
import pytest
from bash_security_hook import is_destructive, block_destructive_command

class TestBashSecurityHook:
    def test_block_rm_rf(self):
        assert is_destructive("rm -rf /")
        assert is_destructive("rm -rf /home/user")

    def test_block_drop_table(self):
        assert is_destructive("DROP TABLE users")
        assert is_destructive("drop table customers")

    def test_block_git_push_force(self):
        assert is_destructive("git push --force origin main")

    def test_allow_safe_commands(self):
        assert not is_destructive("ls -la")
        assert not is_destructive("echo hello")
        assert not is_destructive("git status")

    def test_block_destructive_returns_error(self):
        result = block_destructive_command("rm -rf /tmp/data")
        assert result["blocked"] is True
        assert "destructive" in result["reason"].lower()

    def test_allow_safe_returns_permitted(self):
        result = block_destructive_command("npm install")
        assert result["blocked"] is False
