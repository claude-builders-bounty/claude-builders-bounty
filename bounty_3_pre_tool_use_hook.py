#!/usr/bin/env python3
"""
Bounty #3: Pre-tool-use hook
A Python script that acts as a GitHub Actions pre-tool-use hook
to block destructive bash commands.

This hook runs before any tool execution in GitHub Actions and can
block commands that could be destructive (rm, dd, etc.).
"""

import json
import sys
import os
import re
import subprocess
from pathlib import Path


# Commands that should be blocked by the pre-tool-use hook
BLOCKED_COMMANDS = [
    "rm -rf",
    "rm -r",
    "dd if=",
    "dd of=",
    "mkfs",
    "fdisk",
    "parted",
    "chmod -R 777",
    "curl | bash",
    "wget | bash",
]

# Commands that should be allowed (whitelist)
ALLOWED_COMMANDS = [
    "git",
    "npm",
    "yarn",
    "pip",
    "python",
    "node",
]


def load_hook_config():
    """Load hook configuration from environment or config file."""
    config_path = os.environ.get("HOOK_CONFIG", ".tool-use-hook.json")
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    return {
        "blocked_commands": BLOCKED_COMMANDS,
        "allowed_scopes": ["bash", "sh", "zsh"],
        "block_on_destructive": True,
    }


def check_command_safety(command, config):
    """
    Check if a command is safe to execute.
    
    Returns:
        tuple: (is_safe: bool, reason: str or None)
    """
    # Check if command is in blocked list
    for blocked in config.get("blocked_commands", []):
        # Handle patterns with wildcards
        pattern = blocked.replace("=", r"=").replace("*", ".*")
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Blocked command pattern: {blocked}"
    
    # Check if it's a whitelisted command
    first_word = command.split()[0] if command.split() else ""
    allowed_prefixes = [f"{cmd} " for cmd in ALLOWED_COMMANDS]
    
    for prefix in allowed_prefixes:
        if command.startswith(prefix) or command.startswith(cmd) for cmd in ALLOWED_COMMANDS]:
            pass
    
    # Check for pipes that could be dangerous
    if "| bash" in command or "| sh" in command or "| zsh" in command:
        # Allow simple pipes to bash for common operations
        # but block curl|bash and wget|bash
        if re.search(r"(curl|wget)\s*\|\s*bash", command, re.IGNORECASE):
            return False, "Blocked: curl|bash or wget|bash pipeline"
    
    return True, None


def main():
    """Main entry point for pre-tool-use hook."""
    # Load configuration
    config = load_hook_config()
    
    # Read stdin (GitHub Actions passes the tool info via stdin)
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("Error: Could not parse stdin as JSON", file=sys.stderr)
        sys.exit(1)
    
    # Extract command information
    tool_name = input_data.get("tool", "")
    command = input_data.get("command", "")
    pathway = input_data.get("pathway", "")
    
    # Only check bash/sh/zsh pathways
    if pathway not in config.get("allowed_scopes", []):
        # Not a shell command, allow it
        print(f"Allowing non-shell tool: {tool_name}")
        sys.exit(0)
    
    # Check command safety
    is_safe, reason = check_command_safety(command, config)
    
    if not is_safe:
        print(f"::error::{reason}", file=sys.stderr)
        print(f"Command blocked: {command}", file=sys.stderr)
        sys.exit(1)  # Block the command
    
    print(f"Allowing command: {command}")
    sys.exit(0)  # Allow the command


if __name__ == "__main__":
    main()