#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code: blocks destructive bash commands.

Claude Code hooks format (settings.json -> hooks.PreToolUse):
  {
    "hooks": {
      "PreToolUse": [
        {
          "matcher": "Bash",
          "hooks": [
            {"type": "command", "command": "python3 ~/.claude/hooks/block_destructive.py"}
          ]
        }
      ]
    }
  }

Install (2 commands):
  1. mkdir -p ~/.claude/hooks
  2. cp block_destructive.py ~/.claude/hooks/ && python3 -c "import json,os;p=os.path.expanduser('~/.claude/settings.json');d=json.load(open(p)) if os.path.exists(p) else {};d.setdefault('hooks',{}).setdefault('PreToolUse',[]).append({'matcher':'Bash','hooks':[{'type':'command','command':'python3 ~/.claude/hooks/block_destructive.py'}]});json.dump(d,open(p,'w'),indent=2)"

Exit code semantics (Claude Code):
  0      -> allow the command (no match)
  2      -> block the command
  other  -> treat as non-match / allow
"""
import json
import os
import re
import sys
import time

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# --- Destructive patterns (regex, case-insensitive) ---
PATTERNS = [
    # SQL: DROP TABLE / TRUNCATE
    (re.compile(r"\bdrop\s+table\b", re.I), "DROP TABLE"),
    (re.compile(r"\btruncate\b", re.I), "TRUNCATE"),
]

# Wholesome context that neutralizes a pattern (e.g. "rm -rf" inside a comment/echo)
SAFE_PREFIX = re.compile(r'^\s*(#|//|echo\b|printf\b|cat\s*<<|: )', re.I)


def _rm_is_destructive(line):
    """Detect `rm` with recursive+force flags (rm -rf, rm -fr, rm -r -f, sudo rm -rf...)."""
    tokens = re.split(r"\s+", line.strip())
    for i, t in enumerate(tokens):
        if t.lower() == "rm":
            flags = []
            for nt in tokens[i + 1:]:
                if nt.startswith("-") and nt not in ("-", "--"):
                    flags.append(nt)
                else:
                    break
            joined = "".join(flags).lower()
            return ("r" in joined and "f" in joined), joined
    return False, ""


def _git_force_push(line):
    """Detect `git push --force` / `git push -f`."""
    tokens = re.split(r"\s+", line.strip())
    for i, t in enumerate(tokens):
        if t.lower() == "git":
            rest = [x.lower() for x in tokens[i + 1:]]
            if rest and rest[0] == "push":
                for tok in rest[1:]:
                    if tok in ("--force", "-f"):
                        return True
                return False
    return False


def _delete_without_where(line):
    """Detect DELETE FROM ... without a WHERE clause in the same statement."""
    if not re.search(r"\bdelete\s+from\b", line, re.I):
        return False
    # evaluate the statement segment up to the next ';'
    seg = line.split(";")[0]
    return not re.search(r"\bwhere\b", seg, re.I)


def check_command(cmd: str):
    """Return (blocked: bool, reason: str|None)."""
    if not cmd or not cmd.strip():
        return False, None
    # Strip surrounding quotes for display
    display = cmd.strip().strip('"').strip("'")
    if SAFE_PREFIX.match(cmd.strip()):
        return False, None
    d_rf, flags = _rm_is_destructive(cmd)
    if d_rf:
        return True, "pattern 'rm -rf' is destructive"
    if _git_force_push(cmd):
        return True, "pattern 'git push --force/-f' is destructive"
    for pattern, name in PATTERNS:
        if pattern.search(cmd):
            return True, f"pattern '{name}' is destructive"
    if _delete_without_where(cmd):
        return True, "DELETE FROM without WHERE"
    return False, None


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]

    # Claude Code passes structured JSON on stdin for PreToolUse hooks
    payload = None
    try:
        if not sys.stdin.isatty():
            raw = sys.stdin.read()
            if raw.strip():
                payload = json.loads(raw)
    except Exception:
        payload = None

    if payload:
        # Structured mode: extract the bash tool input
        tool_input = payload.get("tool_input") or {}
        cmd = tool_input.get("command") or tool_input.get("input") or ""
        cwd = os.getcwd()
    else:
        # Fallback: first argv is the command, or try env var
        cmd = argv[0] if argv else os.environ.get("CLAUDE_PRE_TOOL_USE_COMMAND", "")
        cwd = os.getcwd()

    if not cmd:
        # Nothing to check -> allow
        print("ALLOW: no command provided")
        return 0

    blocked, reason = check_command(cmd)
    if not blocked:
        print("ALLOW: command is safe")
        return 0

    # Log the blocked attempt
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {reason} | cmd: {cmd.strip()[:500]} | cwd: {cwd}\n")
    except Exception:
        pass

    message = (
        "BLOCKED: this bash command was stopped by the pre-tool-use hook.\n"
        f"Reason: {reason}.\n"
        "Destructive commands (rm -rf, DROP TABLE, TRUNCATE, git push --force, "
        "DELETE FROM without WHERE) are not allowed. "
        "If this was intentional, rephrase the operation into a safe form "
        "(e.g. move to trash, add explicit WHERE, use a new branch + regular push).\n"
        f"Attempted command: {cmd.strip()[:300]}"
    )
    print(message)
    # 2 = block in Claude Code hook protocol
    return 2


if __name__ == "__main__":
    sys.exit(main())