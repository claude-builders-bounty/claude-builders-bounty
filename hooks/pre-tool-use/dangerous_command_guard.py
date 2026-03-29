#!/usr/bin/env python3
"""
Pre-tool-use hook: Dangerous Command Guard
Blocks destructive bash commands before Claude Code executes them.

Claude Code hooks API:
  - Reads JSON from stdin with tool_name and tool_input
  - Outputs JSON: {"decision": "block", "reason": "..."} to block
  - Exits 0 to allow (no output needed)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── ANSI colours (disabled when not a TTY) ──────────────────────────────────
USE_COLOR = sys.stderr.isatty()

def c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text

RED    = lambda t: c("1;31", t)
YELLOW = lambda t: c("1;33", t)
CYAN   = lambda t: c("1;36", t)
BOLD   = lambda t: c("1", t)

# ── Paths ───────────────────────────────────────────────────────────────────
HOOKS_DIR  = Path.home() / ".claude" / "hooks"
BLOCKED_LOG = HOOKS_DIR / "blocked.log"

# ── Pattern catalogue ────────────────────────────────────────────────────────
# Each entry: (compiled_regex, human_reason, severity)
PATTERNS: list[tuple[re.Pattern, str, str]] = [

    # ── Filesystem destruction ───────────────────────────────────────────────
    (re.compile(r"\brm\s+.*-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s", re.I),
     "rm with recursive+force flags (rm -rf …)", "CRITICAL"),
    (re.compile(r"\brm\s+.*-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\s", re.I),
     "rm with force+recursive flags (rm -fr …)", "CRITICAL"),
    # rm -rf / or rm -rf . or rm -rf * without path after flags
    (re.compile(r"\brm\s+(?:-\S+\s+)*-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*(?:\s+\S+)*\s*$", re.I),
     "rm recursive+force (rm -rf)", "CRITICAL"),
    (re.compile(r"\brm\s+(?:-\S+\s+)*-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*(?:\s+\S+)*\s*$", re.I),
     "rm force+recursive (rm -fr)", "CRITICAL"),
    (re.compile(r"\bfind\s+.*--delete\b", re.I),
     "find … --delete (mass file deletion)", "HIGH"),
    (re.compile(r"\bfind\s+.*-delete\b", re.I),
     "find … -delete (mass file deletion)", "HIGH"),
    (re.compile(r"\bdd\s+.*if\s*=\s*/dev/(zero|null|random|urandom)", re.I),
     "dd writing from /dev/zero|null|random (disk wipe)", "CRITICAL"),
    (re.compile(r"\b(mkfs|mke2fs|mkntfs|mkswap)\b", re.I),
     "filesystem format command (mkfs/mke2fs/…)", "CRITICAL"),
    (re.compile(r"\bshred\s+", re.I),
     "shred (secure file deletion)", "HIGH"),
    (re.compile(r">\s*/dev/(sda|sdb|sdc|hda|nvme\d)", re.I),
     "writing directly to a raw block device", "CRITICAL"),

    # ── SQL ──────────────────────────────────────────────────────────────────
    (re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW)\b", re.I),
     "SQL DROP TABLE/DATABASE/SCHEMA/INDEX/VIEW", "CRITICAL"),
    (re.compile(r"\bTRUNCATE\s+(TABLE\s+)?\w+", re.I),
     "SQL TRUNCATE TABLE", "HIGH"),
    # DELETE FROM without a trailing WHERE clause (allow DELETE FROM t WHERE …)
    (re.compile(r"\bDELETE\s+FROM\s+\w+\s*(?:;|$)", re.I),
     "SQL DELETE FROM without WHERE clause", "HIGH"),
    (re.compile(r"\bDELETE\s+FROM\s+\w+\s+WHERE\s+1\s*=\s*1", re.I),
     "SQL DELETE FROM … WHERE 1=1 (deletes everything)", "CRITICAL"),

    # ── Git ──────────────────────────────────────────────────────────────────
    # Match --force but NOT --force-with-lease (the safe alternative)
    (re.compile(r"\bgit\s+push\s+.*(?:--force(?!-with-lease)|-f)\b", re.I),
     "git push --force / -f (overwrites remote history)", "HIGH"),
    (re.compile(r"\bgit\s+reset\s+--hard\s+HEAD[~^]\d*", re.I),
     "git reset --hard HEAD~ (discards commits)", "HIGH"),
    (re.compile(r"\bgit\s+clean\s+.*-[a-zA-Z]*f[a-zA-Z]*d", re.I),
     "git clean -fd (removes untracked files)", "MEDIUM"),
    (re.compile(r"\bgit\s+clean\s+.*-[a-zA-Z]*d[a-zA-Z]*f", re.I),
     "git clean -df (removes untracked files)", "MEDIUM"),

    # ── Kubernetes ───────────────────────────────────────────────────────────
    (re.compile(r"\bkubectl\s+delete\s+(namespace|ns)\b", re.I),
     "kubectl delete namespace (destroys entire namespace)", "CRITICAL"),
    (re.compile(r"\bkubectl\s+delete\s+(all|pods|deployments|services)\s+--all\b", re.I),
     "kubectl delete all --all (mass resource deletion)", "CRITICAL"),
    (re.compile(r"\bkubectl\s+delete\s+.*--all-namespaces\b", re.I),
     "kubectl delete … --all-namespaces", "CRITICAL"),

    # ── Process/system ───────────────────────────────────────────────────────
    (re.compile(r"\bkill\s+(-9\s+)?-1\b"),
     "kill -1 / kill -9 -1 (kills all user processes)", "CRITICAL"),
    (re.compile(r"\b:()\s*\{.*:\|:&\s*\};\s*:", re.I),
     "fork bomb", "CRITICAL"),

    # ── Package destruction ──────────────────────────────────────────────────
    (re.compile(r"\bnpm\s+(uninstall|remove|rm)\s+--save\s+\S+.*&&.*rm\b", re.I),
     "npm uninstall combined with rm", "MEDIUM"),
]

def _getenv_bool(name: str) -> bool:
    return os.environ.get(name, "").lower() in ("1", "true", "yes")


def log_blocked(command: str, reason: str, project: str) -> None:
    """Append a blocked attempt to the audit log."""
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"[{timestamp}] BLOCKED | project={project!r} | reason={reason!r} | cmd={command!r}\n"
    try:
        with BLOCKED_LOG.open("a") as fh:
            fh.write(entry)
    except OSError:
        pass  # never crash the hook over logging


def log_allowed_override(command: str, reason: str, project: str) -> None:
    """Append an audit entry when ALLOW_DANGEROUS overrides a block."""
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = (
        f"[{timestamp}] OVERRIDE_ALLOWED | project={project!r} "
        f"| reason={reason!r} | cmd={command!r}\n"
    )
    try:
        with BLOCKED_LOG.open("a") as fh:
            fh.write(entry)
    except OSError:
        pass


def stderr_banner(command: str, reason: str, severity: str, project: str,
                  overridden: bool = False, dry_run: bool = False) -> None:
    """Print a human-readable warning to stderr."""
    width = 72
    sep = "─" * width

    if overridden:
        header = YELLOW(f"⚠  DANGEROUS COMMAND ALLOWED (ALLOW_DANGEROUS=1 override)")
    elif dry_run:
        header = YELLOW(f"[DRY-RUN] Would block — severity: {severity}")
    else:
        header = RED(f"✗  BLOCKED — severity: {severity}")

    print(f"\n{sep}", file=sys.stderr)
    print(header, file=sys.stderr)
    print(f"{sep}", file=sys.stderr)
    print(f"  {BOLD('Reason  :')} {reason}", file=sys.stderr)
    print(f"  {BOLD('Command :')} {command[:120]}", file=sys.stderr)
    print(f"  {BOLD('Project :')} {project}", file=sys.stderr)
    if not overridden and not dry_run:
        print(f"\n  {CYAN('To allow once:')} ALLOW_DANGEROUS=1 <re-run>", file=sys.stderr)
        print(f"  {CYAN('Audit log    :')} {BLOCKED_LOG}", file=sys.stderr)
    print(f"{sep}\n", file=sys.stderr)


def check_command(command: str) -> tuple[bool, str, str]:
    """
    Returns (is_dangerous, reason, severity).
    Checks every pattern; returns the first match.
    """
    for pattern, reason, severity in PATTERNS:
        if pattern.search(command):
            return True, reason, severity
    return False, "", ""


def main() -> None:
    # Read JSON payload from Claude Code
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Not valid JSON — let it through (not our job to block non-bash tools)
        sys.exit(0)

    tool_name: str = payload.get("tool_name", "")
    tool_input: dict = payload.get("tool_input", {})

    # We only inspect Bash tool calls
    if tool_name != "Bash":
        sys.exit(0)

    command: str = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    project: str = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    # Read env vars at call time so tests can patch os.environ
    DRY_RUN = _getenv_bool("HOOK_DRY_RUN")
    ALLOW_DANGEROUS = _getenv_bool("ALLOW_DANGEROUS")

    is_dangerous, reason, severity = check_command(command)

    if not is_dangerous:
        sys.exit(0)

    # Dry-run mode: explain but don't actually block
    if DRY_RUN:
        stderr_banner(command, reason, severity, project, dry_run=True)
        print(json.dumps({
            "decision": "allow",
            "reason": f"[DRY-RUN] Would have blocked: {reason}",
        }))
        sys.exit(0)

    # Allowlist override
    if ALLOW_DANGEROUS:
        log_allowed_override(command, reason, project)
        stderr_banner(command, reason, severity, project, overridden=True)
        sys.exit(0)  # allow

    # Block the command
    log_blocked(command, reason, project)
    stderr_banner(command, reason, severity, project)

    block_message = (
        f"BLOCKED by dangerous_command_guard: {reason}. "
        f"This command was blocked because it is potentially destructive and irreversible. "
        f"If you are certain this is safe, ask the user to re-run with ALLOW_DANGEROUS=1 "
        f"(this will be audit-logged). "
        f"Command: {command[:200]!r}"
    )

    output = {
        "decision": "block",
        "reason": block_message,
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
