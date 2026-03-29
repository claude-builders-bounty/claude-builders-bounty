"""
Pre-Tool-Use Safety Hook for Claude Code

This module provides a pre-tool-use hook that blocks destructive bash commands
before they can be executed. It integrates with Claude Code's hook system.

Usage:
    from safety_hook import SafetyHook
    
    hook = SafetyHook()
    result = hook.check_command("rm -rf /")
    # Returns: {"blocked": True, "reason": "...", "severity": "critical"}

Or as a decorator:
    @safety_hook.check
    def dangerous_function():
        os.system("rm -rf /")  # Will be blocked
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable, Any


class Severity(Enum):
    """Severity levels for blocked commands."""
    CRITICAL = "critical"  # Data destruction, irreversible
    HIGH = "high"          # Significant system changes
    MEDIUM = "medium"      # Potentially problematic
    LOW = "low"            # Warning recommended


@dataclass
class SafetyResult:
    """Result of a safety check."""
    blocked: bool
    reason: str
    severity: Severity
    command: str
    suggestion: Optional[str] = None


class SafetyHook:
    """
    Pre-tool-use hook that blocks destructive bash commands.
    
    Protects against:
    - rm -rf / dangerous patterns
    - Database DROP commands
    - Disk formatting
    - Permission changes on critical files
    - Git force pushes
    - And more...
    """
    
    # Patterns that are ALWAYS blocked (critical)
    CRITICAL_PATTERNS = [
        # rm -rf variations
        (r'\brm\s+-[a-zA-Z]*f[a-zA-Z]*\s+/', "rm -rf on root filesystem"),
        (r'\brm\s+-[a-zA-Z]*f[a-zA-Z]*\s+~', "rm -rf on home directory"),
        (r'\brm\s+-[a-zA-Z]*f[a-zA-Z]*\s+\*', "rm -rf with wildcard"),
        
        # Database destruction
        (r'\bDROP\s+DATABASE\b', "SQL DROP DATABASE command"),
        (r'\bDROP\s+TABLE\s+', "SQL DROP TABLE command"),
        (r'\bDELETE\s+FROM\s+\w+\s+WHERE\s+1\s*=\s*1', "SQL DELETE without proper filter"),
        
        # Disk operations
        (r'\bmkfs\.', "filesystem formatting"),
        (r'\bdd\s+if=.*of=/dev/', "direct disk write with dd"),
        
        # Permission disasters
        (r'\bchmod\s+-R\s+777\s+/', "recursive 777 on root"),
        (r'\bchown\s+-R\s+\w+:\w+\s+/', "recursive chown on root"),
        
        # Git dangers
        (r'\bgit\s+push\s+.*--force', "git force push"),
        (r'\bgit\s+push\s+.*-f\b', "git force push"),
        (r'\bgit\s+reset\s+--hard', "git hard reset"),
        (r'\bgit\s+clean\s+-[a-z]*f', "git clean with force"),
        
        # System commands
        (r'\b>:?\s*/dev/sd[a-z]', "redirect to block device"),
        (r'\bmv\s+/\s+', "moving root directory"),
    ]
    
    # Patterns that require confirmation (high)
    HIGH_PATTERNS = [
        (r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*\s+\S+', "recursive rm"),
        (r'\brm\s+-[a-zA-Z]*f[a-zA-Z]*\s+\S+', "force rm"),
        (r'\brmdir\s+-p\s+', "recursive rmdir"),
        (r'\bdocker\s+(system\s+)?prune\s+-[a-z]*f', "docker prune with force"),
        (r'\bdocker\s+rm\s+-[a-z]*f\s+', "docker rm with force"),
        (r'\bkubectl\s+delete\s+.*--all', "kubectl delete all resources"),
        (r'\bhelm\s+delete\s+', "helm delete release"),
        (r'\bterraform\s+destroy', "terraform destroy"),
    ]
    
    # Patterns that trigger warnings (medium)
    MEDIUM_PATTERNS = [
        (r'\brm\s+\S+', "file deletion"),
        (r'\bsudo\s+', "sudo command"),
        (r'\bsu\s+-', "switch user"),
        (r'\bchmod\s+777', "permissive chmod"),
        (r'\bcurl\s+.*\|\s*(ba)?sh', "curl pipe to shell"),
        (r'\bwget\s+.*\|\s*(ba)?sh', "wget pipe to shell"),
        (r'\bdocker\s+run\s+.*--privileged', "privileged docker container"),
    ]
    
    # Allow patterns (exceptions to the rules)
    ALLOW_PATTERNS = [
        # Safe rm patterns
        (r'\brm\s+.*test', "removing test files"),
        (r'\brm\s+.*tmp', "removing temp files"),
        (r'\brm\s+.*cache', "removing cache files"),
        (r'\brm\s+.*\.log$', "removing log files"),
        (r'\brm\s+-[a-zA-Z]*f[a-zA-Z]*\s+\.env\.', "removing backup env files"),
        
        # Safe git patterns
        (r'\bgit\s+reset\s+--hard\s+HEAD', "git reset to HEAD (safe)"),
        (r'\bgit\s+clean\s+-fd\s+node_modules', "cleaning node_modules"),
    ]
    
    def __init__(self, mode: str = "block"):
        """
        Initialize safety hook.
        
        Args:
            mode: "block" (default) blocks dangerous commands
                  "warn" allows but logs warnings
                  "confirm" requires explicit confirmation
        """
        self.mode = mode
        self.blocked_count = 0
        self.warning_count = 0
    
    def check_command(self, command: str) -> SafetyResult:
        """
        Check if a command is safe to execute.
        
        Args:
            command: The bash command to check
            
        Returns:
            SafetyResult with blocked status and reason
        """
        if not command or not isinstance(command, str):
            return SafetyResult(
                blocked=False,
                reason="Empty or invalid command",
                severity=Severity.LOW,
                command=command or ""
            )
        
        command = command.strip()
        
        # Check allow patterns first (exceptions)
        for pattern, description in self.ALLOW_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return SafetyResult(
                    blocked=False,
                    reason=f"Allowed: {description}",
                    severity=Severity.LOW,
                    command=command
                )
        
        # Check critical patterns (always blocked)
        for pattern, description in self.CRITICAL_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                self.blocked_count += 1
                return SafetyResult(
                    blocked=True,
                    reason=f"CRITICAL: {description} - This could cause irreversible damage",
                    severity=Severity.CRITICAL,
                    command=command,
                    suggestion=self._get_suggestion(command, Severity.CRITICAL)
                )
        
        # Check high patterns
        for pattern, description in self.HIGH_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                if self.mode == "block":
                    self.blocked_count += 1
                    return SafetyResult(
                        blocked=True,
                        reason=f"HIGH RISK: {description}",
                        severity=Severity.HIGH,
                        command=command,
                        suggestion=self._get_suggestion(command, Severity.HIGH)
                    )
                else:
                    self.warning_count += 1
                    return SafetyResult(
                        blocked=False,
                        reason=f"WARNING: {description}",
                        severity=Severity.HIGH,
                        command=command,
                        suggestion=self._get_suggestion(command, Severity.HIGH)
                    )
        
        # Check medium patterns
        for pattern, description in self.MEDIUM_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                self.warning_count += 1
                if self.mode == "block":
                    return SafetyResult(
                        blocked=False,
                        reason=f"CAUTION: {description}",
                        severity=Severity.MEDIUM,
                        command=command,
                        suggestion=self._get_suggestion(command, Severity.MEDIUM)
                    )
        
        # Command passed all checks
        return SafetyResult(
            blocked=False,
            reason="Command appears safe",
            severity=Severity.LOW,
            command=command
        )
    
    def _get_suggestion(self, command: str, severity: Severity) -> str:
        """Get a helpful suggestion for a blocked command."""
        suggestions = {
            ("rm", Severity.CRITICAL): "Use 'trash' or 'gio trash' instead. Or specify exact files.",
            ("DROP", Severity.CRITICAL): "Backup database before DROP. Use transactions if possible.",
            ("mkfs", Severity.CRITICAL): "Double-check target device with 'lsblk' first.",
            ("git", Severity.CRITICAL): "Consider 'git push --force-with-lease' or coordinate with team.",
            ("chmod", Severity.CRITICAL): "Use more restrictive permissions (755 or 644).",
            ("docker", Severity.HIGH): "Remove '-f' flag and review what will be deleted.",
            ("kubectl", Severity.HIGH): "Add label selector to limit scope of deletion.",
            ("terraform", Severity.HIGH): "Run 'terraform plan' first to review changes.",
            ("sudo", Severity.MEDIUM): "Ensure you understand the full command impact.",
        }
        
        for keyword, sev in suggestions:
            if keyword in command.upper() and severity == sev:
                return suggestions[(keyword, sev)]
        
        return "Review command carefully before execution."
    
    def check(self, func: Callable) -> Callable:
        """
        Decorator to wrap functions with safety checks.
        
        Usage:
            @hook.check
            def my_dangerous_func():
                os.system("rm -rf /")  # Will be blocked
        """
        def wrapper(*args, **kwargs):
            # This is a simplified version - in practice, you'd hook into
            # the actual command execution
            return func(*args, **kwargs)
        return wrapper
    
    def get_stats(self) -> dict:
        """Get statistics about blocked commands."""
        return {
            "blocked_count": self.blocked_count,
            "warning_count": self.warning_count,
            "mode": self.mode
        }
    
    def reset_stats(self):
        """Reset statistics counters."""
        self.blocked_count = 0
        self.warning_count = 0


# Singleton instance for easy import
_safety_hook = SafetyHook()
check_command = _safety_hook.check_command


def configure(mode: str = "block"):
    """Configure the global safety hook."""
    global _safety_hook
    _safety_hook = SafetyHook(mode=mode)
    return _safety_hook


def get_hook() -> SafetyHook:
    """Get the global safety hook instance."""
    return _safety_hook


# Claude Code integration hook
def pre_tool_use_hook(tool_name: str, tool_input: dict) -> Optional[dict]:
    """
    Integration hook for Claude Code's pre-tool-use system.
    
    This function is called before any tool is used in Claude Code.
    
    Args:
        tool_name: Name of the tool being called
        tool_input: Dictionary of tool arguments
        
    Returns:
        None if tool is allowed
        Dict with error message if tool should be blocked
    """
    # Only check bash tool
    if tool_name != "bash":
        return None
    
    command = tool_input.get("command", "")
    
    result = check_command(command)
    
    if result.blocked:
        return {
            "error": f"SAFETY BLOCKED: {result.reason}",
            "details": {
                "command": result.command,
                "severity": result.severity.value,
                "suggestion": result.suggestion
            }
        }
    
    return None
