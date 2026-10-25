#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code that intercepts and blocks destructive Bash commands.

Usage:
    from pre_tool_hook import CommandInterceptor

    interceptor = CommandInterceptor()
    # This will raise a DangerousCommandError if the command is unsafe
    interceptor.run("rm -rf /tmp/somefile")
"""

import re
import shlex
import subprocess
from typing import List


class DangerousCommandError(RuntimeError):
    """Raised when a command is identified as dangerous."""
    pass


class CommandInterceptor:
    """
    Intercepts Bash commands and blocks those that match known destructive patterns.
    """

    # Regex patterns for destructive commands (case‑insensitive)
    _dangerous_patterns: List[re.Pattern] = [
        # rm with -rf or recursive deletion of root or important dirs
        re.compile(r'\brm\s+(-[rf]+|\-?f\s+-?r)\b', re.IGNORECASE),
        re.compile(r'\brm\s+.*\b/(\*|\.{2,}|\.|/)?\b', re.IGNORECASE),

        # Disk‑wiping utilities
        re.compile(r'\bdd\s+.*\bif=.*\bof=.*\b', re.IGNORECASE),
        re.compile(r'\bmkfs\.', re.IGNORECASE),

        # Fork bomb
        re.compile(r':\s*\(\s*\)\s*{\s*:\s*\|\s*:\s*;\s*}&', re.IGNORECASE),

        # System power commands
        re.compile(r'\b(shutdown|reboot|halt|poweroff)\b', re.IGNORECASE),

        # Killing processes indiscriminately
        re.compile(r'\bkill\s+(-9\s+)?-?\d+\b', re.IGNORECASE),
        re.compile(r'\bkillall\s+.+', re.IGNORECASE),

        # Overwriting device files
        re.compile(r'>\s*/dev/(sda|sdb|sd[c-z]|mmcblk[0-9]|nvme[0-9]n[0-9])', re.IGNORECASE),

        # Overwriting critical system files
        re.compile(r'>\s*/(etc|var|usr|bin|sbin|lib|opt|boot)/', re.IGNORECASE),

        # Redirection to /dev/null that discards output of dangerous commands
        re.compile(r'\b(rm|dd|mkfs|shutdown|reboot|halt|poweroff|kill|killall)\b.*>\s*/dev/null', re.IGNORECASE),

        # Any command that contains " :(){ :|:& };:" (alternative fork bomb syntax)
        re.compile(r':\(\)\s*{\s*:\s*\|\s*:\s*;\s*}&', re.IGNORECASE),
    ]

    def __init__(self, logger=None):
        """
        Initialize the interceptor.

        :param logger: Optional logger with .info/.warning/.error methods.
        """
        self.logger = logger

    def _log(self, level: str, msg: str):
        if self.logger:
            getattr(self.logger, level)(msg)
        else:
            print(f"[{level.upper()}] {msg}")

    def is_safe(self, command: str) -> bool:
        """
        Determine whether a command is safe to execute.

        :param command: The raw command string.
        :return: True if safe, False otherwise.
        """
        # Strip leading/trailing whitespace for reliable matching
        cmd = command.strip()

        # Quick reject empty commands
        if not cmd:
            self._log('info', 'Empty command considered safe.')
            return True

        # Check each dangerous pattern
        for pattern in self._dangerous_patterns:
            if pattern.search(cmd):
                self._log('warning', f'Dangerous pattern detected: {pattern.pattern}')
                self._log('warning', f'Command blocked: {cmd}')
                return False

        # Additional heuristic: block any command that tries to write directly to a block device
        tokens = shlex.split(cmd)
        for token in tokens:
            if token.startswith('/dev/') and any(dev in token for dev in ('sd', 'mmcblk', 'nvme')):
                self._log('warning', f'Attempt to write to block device: {token}')
                return False

        self._log('info', f'Command deemed safe: {cmd}')
        return True

    def run(self, command: str, capture_output: bool = True, check: bool = True, **subprocess_kwargs):
        """
        Execute a command after safety validation.

        :param command: Bash command string.
        :param capture_output: Whether to capture stdout/stderr (default True).
        :param check: Whether to raise CalledProcessError on non‑zero exit (default True).
        :param subprocess_kwargs: Additional arguments passed to subprocess.run.
        :return: subprocess.CompletedProcess instance.
        :raises DangerousCommandError: If the command is deemed unsafe.
        """
        if not self.is_safe(command):
            raise DangerousCommandError(f'Blocked potentially destructive command: {command!r}')

        self._log('info', f'Executing command: {command}')
        result = subprocess.run(
            command,
            shell=True,
            capture_output=capture_output,
            text=True,
            check=check,
            **subprocess_kwargs
        )
        self._log('info', f'Command finished with return code {result.returncode}')
        return result


# Example usage (remove or comment out when integrating into Claude Code)
if __name__ == '__main__':
    interceptor = CommandInterceptor()
    test_commands = [
        "echo 'Hello, world!'",
        "rm -rf /tmp/somefile",
        "dd if=/dev/zero of=/dev/sda bs=1M count=10",
        "shutdown -h now",
        "ls -l /",
    ]

    for cmd in test_commands:
        try:
            out = interceptor.run(cmd)
            print(f"OUTPUT:\n{out.stdout}")
        except DangerousCommandError as e:
            print(f"BLOCKED: {e}")
        except subprocess.CalledProcessError as e:
            print(f"ERROR ({e.returncode}): {e.stderr}")