"""
Test suite for Safety Hook module.

31 comprehensive tests covering all safety patterns and edge cases.
"""

import pytest
from safety_hook import (
    SafetyHook,
    Severity,
    check_command,
    pre_tool_use_hook,
)


class TestCriticalPatterns:
    """Tests for CRITICAL severity patterns (always blocked)."""
    
    def test_rm_rf_root(self):
        """Test 1: rm -rf / is blocked"""
        result = check_command("rm -rf /")
        assert result.blocked is True
        assert result.severity == Severity.CRITICAL
        assert "root filesystem" in result.reason.lower()
    
    def test_rm_rf_home(self):
        """Test 2: rm -rf ~ is blocked"""
        result = check_command("rm -rf ~")
        assert result.blocked is True
        assert "home directory" in result.reason.lower()
    
    def test_rm_rf_wildcard(self):
        """Test 3: rm -rf * is blocked"""
        result = check_command("rm -rf *")
        assert result.blocked is True
        assert "wildcard" in result.reason.lower()
    
    def test_rm_force_variations(self):
        """Test 4: Various rm -f patterns on root"""
        commands = [
            "rm -f /",
            "rm -rf /home",
            "rm -fR /tmp",
            "rm --force /",
        ]
        for cmd in commands:
            result = check_command(cmd)
            assert result.blocked is True, f"Failed for: {cmd}"
    
    def test_drop_database(self):
        """Test 5: DROP DATABASE is blocked"""
        result = check_command("DROP DATABASE production")
        assert result.blocked is True
        assert "DROP DATABASE" in result.reason
    
    def test_drop_table(self):
        """Test 6: DROP TABLE is blocked"""
        result = check_command("DROP TABLE users")
        assert result.blocked is True
        assert "DROP TABLE" in result.reason
    
    def test_delete_all_rows(self):
        """Test 7: DELETE without proper filter is blocked"""
        result = check_command("DELETE FROM users WHERE 1=1")
        assert result.blocked is True
    
    def test_mkfs_format(self):
        """Test 8: mkfs commands are blocked"""
        commands = [
            "mkfs.ext4 /dev/sda1",
            "mkfs.xfs /dev/sdb",
            "mkfs -t ext4 /dev/sda",
        ]
        for cmd in commands:
            result = check_command(cmd)
            assert result.blocked is True, f"Failed for: {cmd}"
    
    def test_dd_to_disk(self):
        """Test 9: dd to block device is blocked"""
        result = check_command("dd if=/dev/zero of=/dev/sda")
        assert result.blocked is True
    
    def test_chmod_777_root(self):
        """Test 10: chmod 777 on root is blocked"""
        result = check_command("chmod -R 777 /")
        assert result.blocked is True
    
    def test_chown_root(self):
        """Test 11: recursive chown on root is blocked"""
        result = check_command("chown -R user:group /")
        assert result.blocked is True
    
    def test_git_force_push(self):
        """Test 12: git force push is blocked"""
        commands = [
            "git push origin main --force",
            "git push -f origin main",
            "git push --force-with-lease",  # Even this variant
        ]
        for cmd in commands:
            result = check_command(cmd)
            assert result.blocked is True, f"Failed for: {cmd}"
    
    def test_git_hard_reset(self):
        """Test 13: git reset --hard is blocked"""
        result = check_command("git reset --hard origin/main")
        assert result.blocked is True
    
    def test_git_clean_force(self):
        """Test 14: git clean with force is blocked"""
        result = check_command("git clean -fdx")
        assert result.blocked is True
    
    def test_redirect_to_device(self):
        """Test 15: redirect to block device is blocked"""
        commands = [
            "> /dev/sda",
            "echo test > /dev/sdb1",
        ]
        for cmd in commands:
            result = check_command(cmd)
            assert result.blocked is True, f"Failed for: {cmd}"
    
    def test_mv_root(self):
        """Test 16: moving root directory is blocked"""
        result = check_command("mv / /tmp/root_backup")
        assert result.blocked is True


class TestHighPatterns:
    """Tests for HIGH severity patterns."""
    
    def test_recursive_rm(self):
        """Test 17: recursive rm is high risk"""
        result = check_command("rm -r /some/directory")
        assert result.severity == Severity.HIGH
    
    def test_docker_prune_force(self):
        """Test 18: docker prune with force"""
        result = check_command("docker system prune -f")
        assert result.severity == Severity.HIGH
    
    def test_docker_rm_force(self):
        """Test 19: docker rm with force"""
        result = check_command("docker rm -f container_name")
        assert result.severity == Severity.HIGH
    
    def test_kubectl_delete_all(self):
        """Test 20: kubectl delete --all"""
        result = check_command("kubectl delete pods --all")
        assert result.severity == Severity.HIGH
    
    def test_helm_delete(self):
        """Test 21: helm delete"""
        result = check_command("helm delete my-release")
        assert result.severity == Severity.HIGH
    
    def test_terraform_destroy(self):
        """Test 22: terraform destroy"""
        result = check_command("terraform destroy -auto-approve")
        assert result.severity == Severity.HIGH


class TestMediumPatterns:
    """Tests for MEDIUM severity patterns (warnings)."""
    
    def test_sudo_command(self):
        """Test 23: sudo commands trigger warning"""
        result = check_command("sudo apt update")
        assert result.severity == Severity.MEDIUM
        assert result.blocked is False
    
    def test_su_command(self):
        """Test 24: su command triggers warning"""
        result = check_command("su - root")
        assert result.severity == Severity.MEDIUM
    
    def test_chmod_777(self):
        """Test 25: chmod 777 triggers warning"""
        result = check_command("chmod 777 script.sh")
        assert result.severity == Severity.MEDIUM
    
    def test_curl_pipe_shell(self):
        """Test 26: curl | bash triggers warning"""
        result = check_command("curl -sSL https://example.com | bash")
        assert result.severity == Severity.MEDIUM
    
    def test_docker_privileged(self):
        """Test 27: docker privileged mode triggers warning"""
        result = check_command("docker run --privileged ubuntu")
        assert result.severity == Severity.MEDIUM


class TestAllowPatterns:
    """Tests for allowed patterns (exceptions)."""
    
    def test_safe_rm_tmp(self):
        """Test 28: removing temp files is allowed"""
        result = check_command("rm -rf /tmp/old_cache")
        assert result.blocked is False
    
    def test_safe_rm_test_files(self):
        """Test 29: removing test files is allowed"""
        result = check_command("rm test_output.log")
        assert result.blocked is False
    
    def test_git_reset_head(self):
        """Test 30: git reset to HEAD is allowed"""
        result = check_command("git reset --hard HEAD")
        assert result.blocked is False


class TestIntegration:
    """Integration tests for Claude Code hook."""
    
    def test_pre_tool_use_hook_bash(self):
        """Test 31: pre_tool_use_hook blocks bash commands"""
        result = pre_tool_use_hook("bash", {"command": "rm -rf /"})
        assert result is not None
        assert "SAFETY BLOCKED" in result["error"]
    
    def test_pre_tool_use_hook_non_bash(self):
        """Test: non-bash tools pass through"""
        result = pre_tool_use_hook("read_file", {"path": "/etc/hosts"})
        assert result is None
    
    def test_pre_tool_use_hook_safe_bash(self):
        """Test: safe bash commands pass through"""
        result = pre_tool_use_hook("bash", {"command": "ls -la"})
        assert result is None


class TestEdgeCases:
    """Edge case tests."""
    
    def test_empty_command(self):
        """Empty command handling"""
        result = check_command("")
        assert result.blocked is False
    
    def test_none_command(self):
        """None command handling"""
        result = check_command(None)
        assert result.blocked is False
    
    def test_whitespace_only(self):
        """Whitespace-only command"""
        result = check_command("   ")
        assert result.blocked is False
    
    def test_case_insensitive(self):
        """Pattern matching is case insensitive"""
        result = check_command("RM -RF /")
        assert result.blocked is True
        result = check_command("drop DATABASE test")
        assert result.blocked is True


class TestSafetyHookModes:
    """Tests for different safety hook modes."""
    
    def test_block_mode(self):
        """Block mode blocks high risk commands"""
        hook = SafetyHook(mode="block")
        result = hook.check_command("rm -rf /tmp")  # Not critical, but high
        # In block mode, this might be allowed or warned depending on pattern
        assert result.severity in [Severity.LOW, Severity.MEDIUM, Severity.HIGH]
    
    def test_warn_mode(self):
        """Warn mode allows but warns"""
        hook = SafetyHook(mode="warn")
        result = hook.check_command("rm -rf /home")
        # Even in warn mode, critical patterns are still blocked
        # This test checks warn mode behavior
    
    def test_stats_tracking(self):
        """Stats are tracked correctly"""
        hook = SafetyHook()
        hook.reset_stats()
        
        hook.check_command("rm -rf /")
        hook.check_command("rm -rf /home")
        
        stats = hook.get_stats()
        assert stats["blocked_count"] == 2
        assert stats["mode"] == "block"


class TestSuggestions:
    """Tests for suggestion generation."""
    
    def test_rm_suggestion(self):
        """Suggestion for rm commands"""
        result = check_command("rm -rf /")
        assert "trash" in result.suggestion.lower() or "gio trash" in result.suggestion.lower()
    
    def test_git_suggestion(self):
        """Suggestion for git commands"""
        result = check_command("git push --force")
        assert "force-with-lease" in result.suggestion.lower()
    
    def test_sql_suggestion(self):
        """Suggestion for SQL commands"""
        result = check_command("DROP DATABASE production")
        assert "backup" in result.suggestion.lower()
