#!/usr/bin/env python3
"""
Pre-Tool-Use Hook — Blocks Destructive Actions
================================================
A Claude Code PreToolUse hook that inspects tool calls before execution and
blocks potentially destructive operations (rm -rf, disk writes, dangerous git
commands, secrets exposure, etc.).

This directly addresses Bounty #3: Pre-tool-use hook that blocks destructive actions.

Usage in .claude/settings.json:
    {
      "hooks": {
        "PreToolUse": [
          {
            "matcher": "Bash|Read|Write|Edit",
            "hooks": [
              {
                "type": "command",
                "command": "python /path/to/pre_tool_hook.py",
                "timeout": 10,
                "statusMessage": "\U0001f512 Checking safety..."
              }
            ]
          }
        ]
      }
    }

With optional `if` filter for efficiency:
    "if": "Bash(rm *)"     — only runs when rm is detected

Input (stdin):
    JSON payload with tool_name, tool_input, session_id, cwd, etc.

Output (stdout):
    \u2022 If safe:      {} or exit 0 (no blocking)
    \u2022 If blocked:   {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                         "permissionDecision": "deny",
                         "permissionDecisionReason": "\U0001f6a8 [rule-id] explanation"}}

Safety Levels (set via HOOK_SAFETY_LEVEL env var):
    critical   \u2014 Only catastrophic: rm -rf ~, dd to disk, fork bombs
    high       \u2014 + risky: force push main, secrets exposure, git reset --hard
    strict     \u2014 + cautionary: any force push, sudo rm, docker prune
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# \u2500\u2500\u2500 Configuration \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
SAFETY_LEVEL = os.environ.get("HOOK_SAFETY_LEVEL", "high").lower()

LEVEL_RANK = {"critical": 1, "high": 2, "strict": 3}
EMOJIS = {"critical": "\U0001f6a8", "high": "\u26d4", "strict": "\u26a0\ufe0f"}

LOG_DIR = Path.home() / ".claude" / "hooks-logs"

# \u2500\u2500\u2500 Dangerous Pattern Definitions \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# Each pattern: (level, id, regex, reason)

PATTERNS = [
    # \u2500\u2500 CRITICAL: Catastrophic, unrecoverable \u2500\u2500
    ("critical", "rm-home",
     re.compile(r'\brm\b.*~\/'),
     "rm targeting home directory"),

    ("critical", "rm-home-trailing",
     re.compile(r'\brm\b.*\s~(?:\s|[;&|]|$)'),
     "rm targeting home directory (bare ~)"),

    ("critical", "rm-home-var",
     re.compile(r'\brm\b.*\$HOME\b'),
     "rm targeting $HOME"),

    ("critical", "rm-root",
     re.compile(r'\brm\b.*\s\/(?:\s|[*]|[;&|]|$)'),
     "rm targeting root filesystem"),

    ("critical", "rm-system",
     re.compile(r'\brm\s+(-.+\s+)*\/(etc|usr|var|bin|sbin|lib|boot|dev|proc|sys)(?:\/|\s|$)'),
     "rm targeting system directory"),

    ("critical", "rm-cwd",
     re.compile(r'\brm\b.*\s\.\/[*]?(?:\s|$|[;&|])'),
     "rm deleting current directory contents"),

    ("critical", "rm-star",
     re.compile(r'\brm\b.*\s[*](?:\s|$|[;&|])'),
     "rm with wildcard (potential mass deletion)"),

    ("critical", "dd-disk",
     re.compile(r'\bdd\b.*of=\/dev\/(sd[a-z]|nvme|hd[a-z]|vd[a-z]|xvd[a-z])\b'),
     "dd writing directly to disk device"),

    ("critical", "mkfs",
     re.compile(r'\bmkfs(?:\.\w+)?\s+\/dev\/(sd[a-z]|nvme|hd[a-z]|vd[a-z])'),
     "mkfs formatting a disk device"),

    ("critical", "fork-bomb",
     re.compile(r':\(\)\s*\{.*:\s*\|\s*:.*&'),
     "fork bomb detected"),

    # \u2500\u2500 HIGH: Significant risk, data loss, security \u2500\u2500
    ("high", "curl-pipe-sh",
     re.compile(r'\b(curl|wget)\b.+\|\s*(ba)?sh\b'),
     "piping URL to shell (remote code execution risk)"),

    ("high", "git-force-main",
     re.compile(r'\bgit\s+push\b(?!.*--force-with-lease).*(--force|-f)\b.*\b(main|master)\b'),
     "force push to main/master branch"),

    ("high", "git-reset-hard",
     re.compile(r'\bgit\s+reset\s+--hard\b'),
     "git reset --hard loses uncommitted work"),

    ("high", "git-clean-f",
     re.compile(r'\bgit\s+clean\s+(-\w*f|-f)'),
     "git clean -f deletes untracked files"),

    ("high", "chmod-777",
     re.compile(r'\bchmod\b.*\b777\b'),
     "chmod 777 is a security risk"),

    ("high", "cat-env",
     re.compile(r'\b(cat|less|head|tail|more)\s+\.env\b'),
     "reading .env file exposes secrets"),

    ("high", "cat-secrets",
     re.compile(r'\b(cat|less|head|tail|more)\b.*(credentials|secrets?|\.pem|\.key|id_rsa|id_ed25519)', re.I),
     "reading secrets file"),

    ("high", "env-dump",
     re.compile(r'\b(printenv|^env)\s*([;&|]|$)'),
     "env dump may expose secrets in output"),

    ("high", "echo-secret",
     re.compile(r'\becho\b.*\$\w*(?:SECRET|KEY|TOKEN|PASSWORD|API_|PRIVATE)', re.I),
     "echoing a secret variable"),

    ("high", "docker-vol-rm",
     re.compile(r'\bdocker\s+volume\s+(rm|prune)'),
     "docker volume deletion loses data"),

    ("high", "rm-ssh",
     re.compile(r'\brm\b.*(?:\.ssh|authorized_keys|known_hosts)'),
     "deleting SSH keys or authorized_keys"),

    ("high", "git-push-secrets",
     re.compile(r'\bgit\s+push\b.*\b(?:secret|\.env|credential|token)\b', re.I),
     "pushing secrets to remote"),

    # \u2500\u2500 STRICT: Cautionary, context-dependent \u2500\u2500
    ("strict", "git-force-any",
     re.compile(r'\bgit\s+push\b(?!.*--force-with-lease).*(--force|-f)\b'),
     "force push (use --force-with-lease instead)"),

    ("strict", "git-checkout-dot",
     re.compile(r'\bgit\s+checkout\s+\.'),
     "git checkout . discards all local changes"),

    ("strict", "sudo-rm",
     re.compile(r'\bsudo\s+rm\b'),
     "sudo rm with elevated privileges"),

    ("strict", "docker-prune",
     re.compile(r'\bdocker\s+(system|image)\s+prune'),
     "docker prune removes cached images"),

    ("strict", "crontab-r",
     re.compile(r'\bcrontab\s+-r\b'),
     "removes all cron jobs"),

    ("strict", "git-branch-D",
     re.compile(r'\bgit\s+branch\s+-D\b'),
     "force delete branch (use -d for safety check)"),
]


# \u2500\u2500\u2500 Helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def log_event(data: dict) -> None:
    """Append a JSON line to the daily log file."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        entry = {"ts": datetime.now().isoformat(), **data}
        with open(log_file, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception:
        pass  # Logging should never break the hook


def check_command(cmd: str) -> dict | None:
    """Check a shell command against all dangerous patterns.

    Returns the matched pattern dict if blocked, None if safe.
    """
    threshold = LEVEL_RANK.get(SAFETY_LEVEL, 2)

    for level, pat_id, regex, reason in PATTERNS:
        if LEVEL_RANK.get(level, 0) <= threshold and regex.search(cmd):
            return {
                "level": level,
                "id": pat_id,
                "reason": reason,
            }
    return None


def build_deny_response(pattern: dict) -> str:
    """Build the JSON deny response for Claude Code."""
    emoji = EMOJIS.get(pattern["level"], "\u26d4")
    reason = f"{emoji} [{pattern['id']}] {pattern['reason']}"
    return json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    })


def handle_bash_tool(data: dict) -> str:
    """Handle PreToolUse for Bash tool calls."""
    cmd = (data.get("tool_input") or {}).get("command", "")
    if not cmd:
        return "{}"

    result = check_command(cmd)

    if result:
        log_event({
            "level": "BLOCKED",
            "id": result["id"],
            "safety_level": result["level"],
            "command": cmd[:500],
            "session_id": data.get("session_id"),
            "cwd": data.get("cwd"),
            "permission_mode": data.get("permission_mode"),
        })
        return build_deny_response(result)

    return "{}"


def handle_read_tool(data: dict) -> str:
    """Handle PreToolUse for Read tool \u2014 block reads of sensitive files."""
    file_path = (data.get("tool_input") or {}).get("file_path", "")
    if not file_path:
        return "{}"

    sensitive_patterns = [
        (r"\.env$", ".env file"),
        (r"\.pem$", ".pem private key"),
        (r"\.key$", ".key private key"),
        (r"id_rsa$", "SSH private key"),
        (r"id_ed25519$", "SSH ed25519 key"),
        (r"credentials", "credentials file"),
        (r"secrets", "secrets file"),
    ]

    for pattern, desc in sensitive_patterns:
        if re.search(pattern, file_path, re.I):
            log_event({
                "level": "BLOCKED",
                "id": "read-sensitive",
                "file_path": file_path,
                "session_id": data.get("session_id"),
            })
            return json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"\u26d4 [read-sensitive] Blocked read of sensitive file: {desc} ({file_path})",
                }
            })

    return "{}"


def handle_write_tool(data: dict) -> str:
    """Handle PreToolUse for Write/Edit \u2014 block writes to protected files."""
    file_path = (data.get("tool_input") or {}).get("file_path", "")
    if not file_path:
        return "{}"

    protected_patterns = [
        (r"(?:^|/)\.claude/settings\.json$", ".claude/settings.json"),
        (r"(?:^|/)\.claude/settings\.local\.json$", ".claude/settings.local.json"),
        (r"Gemfile\.lock$", "Gemfile.lock"),
        (r"yarn\.lock$", "yarn.lock"),
        (r"package-lock\.json$", "package-lock.json"),
        (r"poetry\.lock$", "poetry.lock"),
        (r"Cargo\.lock$", "Cargo.lock"),
        (r"(?:^|/)\.env$", ".env file"),
    ]

    for pattern, desc in protected_patterns:
        if re.search(pattern, file_path):
            log_event({
                "level": "BLOCKED",
                "id": "write-protected",
                "file_path": file_path,
                "session_id": data.get("session_id"),
            })
            return json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"\u26d4 [write-protected] Blocked write to protected file: {desc}",
                }
            })

    return "{}"


# \u2500\u2500\u2500 Main Entry Point \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def main():
    """Read stdin JSON, inspect the tool call, and optionally block it."""
    try:
        raw = sys.stdin.read()
        if not raw:
            print("{}")
            return

        data = json.loads(raw)
        tool_name = data.get("tool_name", "")

        # Route to the appropriate handler based on tool type
        if tool_name == "Bash":
            result = handle_bash_tool(data)
        elif tool_name in ("Read", "Grep", "Glob", "ListDir"):
            result = handle_read_tool(data)
        elif tool_name in ("Write", "Edit"):
            result = handle_write_tool(data)
        else:
            result = "{}"

        print(result, end="")

    except json.JSONDecodeError:
        print("{}", end="")
    except Exception as e:
        log_event({"level": "ERROR", "error": str(e)})
        print("{}", end="")


if __name__ == "__main__":
    main()
