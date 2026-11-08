#!/usr/bin/env python3
"""Destructor Guard - a Claude Code PreToolUse hook that blocks destructive bash commands.

Protocol (Claude Code PreToolUse):
  * Reads the hook JSON from stdin: {"tool_name": "Bash", "tool_input": {"command": "..."}}
  * If the command matches a known destructive pattern it logs the attempt and
    exits with code 2 (Claude Code cancels the tool call) with a clear,
    human-readable message on stderr (plus the modern JSON "decision":"block"
    payload on stdout for newer clients).
  * Anything that does not match exits 0 and the command runs normally.

Two-command install:
  1) curl -fsSL https://raw.githubusercontent.com/7777add7777-ai/claude-builders-bounty/hook-destructor-guard/hooks/destructor_guard.py -o ~/.claude/destructor_guard.py
  2) python3 <(curl -fsSL https://raw.githubusercontent.com/7777add7777-ai/claude-builders-bounty/hook-destructor-guard/hooks/install_destructor_guard.py)

Log file: ~/.claude/destructor-guard.log (override with DESTRUCTOR_GUARD_LOG)
"""
import datetime
import json
import os
import re
import sys

LOG_FILE = os.path.expanduser(
    os.environ.get("DESTRUCTOR_GUARD_LOG", "~/.claude/destructor-guard.log")
)

BLOCK_DEVICE = r"(sd[a-z]+|nvme[0-9]+n[0-9]+p?[0-9]*|hd[a-z]+|mmcblk[0-9]+p?[0-9]*)"


def check_rm(cmd):
    """rm -r/-R (or --recursive) targeting /, ~, $HOME or /*."""
    for m in re.finditer(r"\brm\b([^\n|;&`]*)", cmd):
        tokens = m.group(1).split()
        flags, targets = [], []
        for tok in tokens:
            if tok.startswith("--"):
                if tok == "--recursive":
                    flags.append("r")
            elif tok.startswith("-"):
                flags.append(tok)
            else:
                targets.append(tok)
        recursive = any(("r" in f or "R" in f) for f in flags)
        if not recursive:
            continue
        for t in targets:
            if t in ("/", "//", "~", "$HOME", "/*", "~/*"):
                return "rm with -r/-R targets %s" % t
    return None


def check_force_push(cmd):
    """git push --force / -f / --force-with-lease to main or master (or --mirror)."""
    for m in re.finditer(r"\bgit\s+push\b([^\n|;&`]*)", cmd):
        rest = m.group(1)
        force = re.search(r"--force\b|--force-with-lease\b|(^|\s)-f(\s|$)", rest)
        if not force:
            continue
        if re.search(r"--mirror\b", rest):
            return "git push --mirror with force (rewrites all remote branches incl. main/master)"
        if re.search(r"\b(main|master)\b", rest):
            return "git push --force to main/master"
    return None


def check_sql(cmd):
    m = re.search(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", cmd, re.IGNORECASE)
    if m:
        return "SQL " + m.group(0).upper()
    m = re.search(r"\bTRUNCATE\s+([A-Za-z_][\w.]*)", cmd, re.IGNORECASE)
    if m:
        return "SQL TRUNCATE " + m.group(1)
    return None


def check_mkfs(cmd):
    m = re.search(r"\bmkfs(\.\w+)?\b", cmd)
    if m:
        return "mkfs (formats a partition)"
    return None


def check_dd(cmd):
    m = re.search(r"\bdd\b[^|\n]*?\bof=/dev/%s" % BLOCK_DEVICE, cmd)
    if m:
        return "dd writing directly to a block device"
    return None


def check_blockdev_write(cmd):
    m = re.search(r">\s*/dev/%s" % BLOCK_DEVICE, cmd)
    if m:
        return "redirecting output into a raw block device"
    return None


def check_chmod(cmd):
    m = re.search(r"\bchmod\s+(?:-\w+\s+)*777\s+(?:-\w+\s+)*(~|/)(?:\s|$)", cmd)
    if m:
        return "chmod -R 777 on %s" % m.group(1)
    return None


def check_fork_bomb(cmd):
    m = re.search(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;", cmd)
    if m:
        return "fork bomb"
    return None


def check_shutdown(cmd):
    m = re.search(r"\b(shutdown|reboot|halt|poweroff)\b", cmd)
    if m:
        return m.group(1) + " (system power action)"
    return None


CHECKS = [
    ("rm of root/home", check_rm),
    ("force push to main/master", check_force_push),
    ("SQL DROP/TRUNCATE", check_sql),
    ("mkfs", check_mkfs),
    ("dd to block device", check_dd),
    ("block device redirect", check_blockdev_write),
    ("chmod -R 777 / or ~", check_chmod),
    ("fork bomb", check_fork_bomb),
    ("shutdown/reboot", check_shutdown),
]


def log_attempt(cmd, reason):
    entry = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "command": cmd[:500],
        "reason": reason,
    }
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass  # logging must never break the hook


def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except (ValueError, TypeError):
        data = {}
    if not isinstance(data, dict):
        sys.exit(0)
    tool_input = data.get("tool_input") or {}
    cmd = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
    if not cmd or not isinstance(cmd, str):
        sys.exit(0)  # not a bash command - let it through

    for label, fn in CHECKS:
        hit = fn(cmd)
        if hit:
            reason = "[destructor-guard] BLOCKED destructive command: %s (%s)." % (hit, label)
            msg = reason + " Command: " + cmd[:300]
            log_attempt(cmd, "%s: %s" % (label, hit))
            print(json.dumps({"decision": "block", "reason": reason}))
            print(msg, file=sys.stderr)
            sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
