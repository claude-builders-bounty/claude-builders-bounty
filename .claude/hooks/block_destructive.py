#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook: Destructive Bash Command Interceptor.

Catches and blocks dangerous operations before they reach the OS:
- rm -rf (recursive & force file removals, all flag and target permutations)
- SQL DROP TABLE, DROP DATABASE, DROP SCHEMA
- git push --force, git push -f, --force-with-lease, +refspecs
- SQL TRUNCATE statements
- SQL DELETE FROM without WHERE clauses
- Raw disk overwrites (mkfs, dd to device nodes)
- Fork bombs and resource exhaustion loops
- System shutdown, reboot, runlevel halts
- Global root permission and ownership wiping (chmod -R 777 /, chown -R ... /)

Protocol Contract:
- Exit code 0: Command permitted (safe).
- Exit code 2: Command blocked (destructive). Reason emitted to stderr, structured JSON to stdout.
- Audit log appended to ~/.claude/hooks/blocked.log (overridable via CLAUDE_HOOK_BLOCKED_LOG or CLAUDE_BLOCKED_LOG_PATH).
"""

import sys
import os
import re
import json
import shlex
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple, List

# Patterns for SQL destructive operations
RE_DROP = re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE)
RE_TRUNCATE = re.compile(r"\bTRUNCATE(\s+TABLE)?\s+[`\"']?[a-zA-Z0-9_\.]+[`\"']?", re.IGNORECASE)
RE_DELETE_FROM = re.compile(r"\bDELETE\s+FROM\s+[`\"']?[a-zA-Z0-9_\.]+[`\"']?", re.IGNORECASE)
RE_WHERE = re.compile(r"\bWHERE\b", re.IGNORECASE)

# Patterns for fork bombs and system disruption
RE_FORK_BOMB = re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:")
RE_WHILE_FORK = re.compile(r"while\s+true\s*;\s*do\s+.*&\s*done", re.IGNORECASE)

# Commands whose arguments are textual or inspection, not destructive executions
SAFE_INSPECTION_COMMANDS = {
    "echo", "printf", "grep", "egrep", "fgrep", "rg", "ag",
    "cat", "sed", "awk", "nano", "vim", "vi", "touch", "mkdir"
}


def get_log_path(cli_override: Optional[str] = None) -> Path:
    """Resolve destination path for blocked.log with environment and CLI override support."""
    if cli_override:
        return Path(cli_override)
    env_override = os.environ.get("CLAUDE_HOOK_BLOCKED_LOG") or os.environ.get("CLAUDE_BLOCKED_LOG_PATH")
    if env_override:
        return Path(env_override)
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked_attempt(command: str, cwd: str, rule: str, reason: str, log_path: Path) -> None:
    """Append structured record to blocked.log."""
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        log_line = f"[{timestamp}] [CWD: {cwd}] [RULE: {rule}] BLOCKED: {command} | REASON: {reason}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write audit log to {log_path}: {e}\n")


def split_compound_commands(cmd_str: str) -> List[str]:
    """Split compound command along shell operators (&&, ||, ;, |, &, \\n), respecting quotes."""
    clauses = []
    current = []
    in_single = False
    in_double = False
    escaped = False
    i = 0
    n = len(cmd_str)

    while i < n:
        c = cmd_str[i]

        if escaped:
            current.append(c)
            escaped = False
            i += 1
            continue

        if c == "\\" and not in_single:
            escaped = True
            current.append(c)
            i += 1
            continue

        if c == "'" and not in_double:
            in_single = not in_single
            current.append(c)
            i += 1
            continue

        if c == '"' and not in_single:
            in_double = not in_double
            current.append(c)
            i += 1
            continue

        if not in_single and not in_double:
            # 2-character operators
            if i + 1 < n and cmd_str[i:i+2] in ("&&", "||"):
                chunk = "".join(current).strip()
                if chunk:
                    clauses.append(chunk)
                current = []
                i += 2
                continue
            # 1-character operators
            if c in (";", "|", "&", "\n"):
                chunk = "".join(current).strip()
                if chunk:
                    clauses.append(chunk)
                current = []
                i += 1
                continue

        current.append(c)
        i += 1

    final_chunk = "".join(current).strip()
    if final_chunk:
        clauses.append(final_chunk)

    return clauses


def extract_subshells_and_nested(cmd_str: str) -> List[str]:
    """Extract nested subshells $(...) and `...` for recursive checking."""
    extracted = []
    # Match $(...)
    for m in re.finditer(r"\$\((.+?)\)", cmd_str):
        extracted.append(m.group(1).strip())
    # Match `...`
    for m in re.finditer(r"`(.+?)`", cmd_str):
        extracted.append(m.group(1).strip())
    return extracted


def strip_wrappers_and_env(tokens: List[str]) -> List[str]:
    """Strip leading environment variables (FOO=bar) and execution wrappers (sudo, env, etc.)."""
    wrappers = {"sudo", "doas", "nohup", "nice", "ionice", "time", "env", "builtin", "command", "exec"}
    i = 0
    while i < len(tokens):
        token = tokens[i]
        # Skip env vars VAR=val
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=.*", token):
            i += 1
            continue
        # Skip wrapper binaries and wrapper flags (like sudo -u root, sudo -E)
        if token in wrappers:
            i += 1
            while i < len(tokens) and tokens[i].startswith("-"):
                # If flag has an argument (e.g. -u root), skip argument too
                if tokens[i] in ("-u", "-g", "-p", "-h", "-C"):
                    i += 2
                else:
                    i += 1
            continue
        break
    return tokens[i:]


def check_rm_rf(tokens: List[str], clause: str) -> Optional[Tuple[str, str]]:
    """Detect if command is 'rm' with both recursive and force flags."""
    if not tokens:
        return None

    cmd = tokens[0].lower()
    # Normalize command binary name
    if cmd in ("rm", "/bin/rm", "/usr/bin/rm") or cmd.endswith("/rm") or cmd.endswith("\\rm"):
        has_r = False
        has_f = False

        for t in tokens[1:]:
            if t == "--":
                break
            if t == "--recursive":
                has_r = True
            elif t == "--force":
                has_f = True
            elif t.startswith("-") and not t.startswith("--"):
                flag_chars = t[1:]
                if "r" in flag_chars or "R" in flag_chars:
                    has_r = True
                if "f" in flag_chars:
                    has_f = True

        if has_r and has_f:
            return ("rm_rf", f"Destructive file deletion: 'rm -rf' detected in '{clause}'")
    return None


def check_git_force(tokens: List[str], clause: str) -> Optional[Tuple[str, str]]:
    """Detect if command is 'git push' with force flags or refspecs."""
    if len(tokens) < 2:
        return None

    cmd = tokens[0].lower()
    if cmd in ("git", "/usr/bin/git", "/bin/git") or cmd.endswith("/git") or cmd.endswith("\\git"):
        if tokens[1].lower() == "push":
            for t in tokens[2:]:
                if t in ("--force", "-f", "--force-with-lease", "--force-if-includes"):
                    return ("git_force", f"Destructive git force push: '{t}' detected in '{clause}'")
                # Detect forced refspecs like +main or +HEAD
                if t.startswith("+") and len(t) > 1:
                    return ("git_force", f"Destructive git forced refspec: '{t}' detected in '{clause}'")
    return None


def check_sql_destructive(tokens: List[str], clause: str) -> Optional[Tuple[str, str]]:
    """Detect destructive SQL statements: DROP, TRUNCATE, DELETE without WHERE."""
    if not tokens:
        return None

    cmd = tokens[0].lower()
    # Ignore safe text/inspection commands where SQL keywords are arguments or search terms
    if cmd in SAFE_INSPECTION_COMMANDS:
        return None
    # If git command other than push (e.g. git commit -m "DROP TABLE"), ignore
    if cmd in ("git", "git.exe"):
        return None

    # Check DROP TABLE / DATABASE / SCHEMA
    drop_match = RE_DROP.search(clause)
    if drop_match:
        return ("drop_table", f"Destructive SQL command: '{drop_match.group(0)}' detected")

    # Check TRUNCATE (differentiate from Unix truncate -s 0 file)
    truncate_match = RE_TRUNCATE.search(clause)
    if truncate_match:
        # If it's the coreutils truncate command with file flags, allow
        if "-s" not in tokens and "--size" not in tokens:
            return ("truncate", f"Destructive SQL command: '{truncate_match.group(0)}' detected")

    # Check DELETE FROM without WHERE
    delete_match = RE_DELETE_FROM.search(clause)
    if delete_match:
        # Extract text from DELETE FROM to statement end (; or end of string)
        stmt_remainder = clause[delete_match.start():]
        end_idx = stmt_remainder.find(";")
        if end_idx != -1:
            stmt_remainder = stmt_remainder[:end_idx]

        if not RE_WHERE.search(stmt_remainder):
            return ("delete_without_where", f"Destructive SQL command: 'DELETE FROM' without WHERE clause detected in '{clause}'")

    return None


def check_raw_disk(tokens: List[str], clause: str) -> Optional[Tuple[str, str]]:
    """Detect raw disk formatting (mkfs) or raw block device overwriting (dd of=/dev/sd*)."""
    if not tokens:
        return None

    cmd = tokens[0].lower()
    if cmd.startswith("mkfs") or cmd == "mke2fs":
        return ("raw_disk", f"Destructive disk formatting command: '{cmd}' detected")

    if cmd == "dd":
        for t in tokens[1:]:
            if t.startswith("of="):
                dest = t[3:].lower()
                dangerous_prefixes = (
                    "/dev/sd", "/dev/hd", "/dev/vd", "/dev/nvme",
                    "/dev/mapper", "/dev/disk", "/dev/mem", "/dev/kmem"
                )
                if any(dest.startswith(p) for p in dangerous_prefixes):
                    return ("raw_disk", f"Destructive raw device write: '{t}' detected in '{clause}'")
    return None


def check_fork_bomb(clause: str) -> Optional[Tuple[str, str]]:
    """Detect classic fork bombs and infinite resource exhaustion loops."""
    if RE_FORK_BOMB.search(clause):
        return ("fork_bomb", "Denial of service: classic bash fork bomb detected")
    if RE_WHILE_FORK.search(clause):
        return ("fork_bomb", "Denial of service: while-fork loop detected")
    return None


def check_system_state(tokens: List[str], clause: str) -> Optional[Tuple[str, str]]:
    """Detect commands that shut down, reboot, or halt system state."""
    if not tokens:
        return None

    cmd = tokens[0].lower()
    if cmd in ("shutdown", "reboot", "poweroff", "halt"):
        return ("system_state", f"System state disruption command: '{cmd}' detected")

    if cmd in ("init", "telinit") and len(tokens) > 1 and tokens[1] in ("0", "6"):
        return ("system_state", f"System runlevel change: '{cmd} {tokens[1]}' detected")

    if cmd == "systemctl" and len(tokens) > 1 and tokens[1] in ("poweroff", "reboot", "halt"):
        return ("system_state", f"System power management command: 'systemctl {tokens[1]}' detected")

    return None


def check_perm_wipe(tokens: List[str], clause: str) -> Optional[Tuple[str, str]]:
    """Detect dangerous recursive permission or ownership changes targeting system roots."""
    if not tokens:
        return None

    cmd = tokens[0].lower()
    critical_targets = {"/", "/*", "/etc", "/var", "/usr", "/boot", "~", "$home"}

    if cmd == "chmod":
        has_recursive = any(t in ("-R", "-r", "--recursive") for t in tokens)
        if has_recursive:
            for t in tokens:
                if t.lower().rstrip("/") in critical_targets or t in ("/", "/*"):
                    return ("perm_wipe", f"Destructive root permission wipe: 'chmod -R' targeting '{t}'")

    if cmd == "chown":
        has_recursive = any(t in ("-R", "-r", "--recursive") for t in tokens)
        if has_recursive:
            for t in tokens:
                if t.lower().rstrip("/") in critical_targets or t in ("/", "/*"):
                    return ("perm_wipe", f"Destructive root ownership wipe: 'chown -R' targeting '{t}'")

    return None


def check_windows_wipes(tokens: List[str], clause: str) -> Optional[Tuple[str, str]]:
    """Detect destructive Windows drive and filesystem wiping commands."""
    if not tokens:
        return None

    cmd = tokens[0].lower()
    if cmd in ("rmdir", "rd"):
        args = [t.lower() for t in tokens[1:]]
        if "/s" in args and "/q" in args:
            for t in args:
                if t in ("c:\\", "c:/", "\\", "c:"):
                    return ("windows_wipe", f"Destructive Windows drive directory removal: '{clause}'")

    if cmd in ("del", "erase"):
        args = [t.lower() for t in tokens[1:]]
        if "/s" in args and ("/f" in args or "/q" in args):
            for t in args:
                if "c:\\" in t or "c:/" in t or t == "*":
                    return ("windows_wipe", f"Destructive Windows file wiping command: '{clause}'")

    if cmd == "format":
        if len(tokens) > 1 and tokens[1].lower().startswith("c:"):
            return ("windows_wipe", f"Destructive Windows drive format command: '{clause}'")

    return None


def check_clause(clause: str) -> Optional[Tuple[str, str]]:
    """Evaluate a single atomic command clause against all security rules."""
    clause = clause.strip()
    if not clause:
        return None

    # Check fork bomb regex before tokenization
    fb = check_fork_bomb(clause)
    if fb:
        return fb

    # Tokenize clause
    try:
        tokens = shlex.split(clause, posix=True)
    except Exception:
        tokens = clause.split()

    if not tokens:
        return None

    # Strip leading env vars and wrappers (sudo, env, etc.)
    clean_tokens = strip_wrappers_and_env(tokens)
    if not clean_tokens:
        return None

    # Check nested shell invocations (e.g. bash -c "rm -rf /")
    cmd = clean_tokens[0].lower()
    if cmd in ("bash", "sh", "zsh", "dash") and len(clean_tokens) >= 3 and clean_tokens[1] == "-c":
        inner_cmd = clean_tokens[2]
        inner_violation = check_command(inner_cmd)
        if inner_violation:
            return inner_violation

    # Run all specific analyzers
    analyzers = [
        lambda: check_rm_rf(clean_tokens, clause),
        lambda: check_git_force(clean_tokens, clause),
        lambda: check_sql_destructive(clean_tokens, clause),
        lambda: check_raw_disk(clean_tokens, clause),
        lambda: check_system_state(clean_tokens, clause),
        lambda: check_perm_wipe(clean_tokens, clause),
        lambda: check_windows_wipes(clean_tokens, clause),
    ]

    for analyzer in analyzers:
        res = analyzer()
        if res:
            return res

    return None


def check_command(command: str) -> Optional[Tuple[str, str]]:
    """
    Main evaluation pipeline.
    Deconstructs compound commands, extracts subshells, and checks all parts.
    Returns (rule_id, reason) if destructive, or None if safe.
    """
    if not command or not command.strip():
        return None

    # Check full command for fork bombs before splitting operators
    fb = check_fork_bomb(command)
    if fb:
        return fb

    # 1. Check extracted subshells $(...) and `...`
    subshells = extract_subshells_and_nested(command)
    for sub in subshells:
        violation = check_command(sub)
        if violation:
            return violation

    # 2. Split compound operators: &&, ||, ;, |, &, \n
    clauses = split_compound_commands(command)
    for clause in clauses:
        violation = check_clause(clause)
        if violation:
            return violation

    return None


def block_and_exit(command: str, cwd: str, rule: str, reason: str, log_path: Path):
    """Log blocked attempt, write diagnostic explanation to stderr, and exit with code 2."""
    log_blocked_attempt(command, cwd, rule, reason, log_path)

    stderr_msg = (
        f"\n[SECURITY HOOK BLOCKED]\n"
        f"Rule:      [{rule}]\n"
        f"Reason:    {reason}\n"
        f"Command:   {command}\n"
        f"Directory: {cwd}\n"
        f"Audit Log: {log_path}\n"
        f"Policy:    Destructive commands are prohibited by safety policy.\n"
    )
    sys.stderr.write(stderr_msg)

    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Command blocked by safety hook [{rule}]: {reason}"
        }
    }
    print(json.dumps(response))
    sys.exit(2)


def allow_and_exit(is_cli_check: bool = False):
    """Exit cleanly with code 0 permitting execution."""
    if is_cli_check:
        print("ALLOWED")
    else:
        response = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow"
            }
        }
        print(json.dumps(response))
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PreToolUse Hook: Destructive Bash Command Interceptor"
    )
    parser.add_argument("--check", type=str, help="Evaluate a command string directly without JSON wrapping")
    parser.add_argument("--cwd", type=str, default=None, help="Current project working directory")
    parser.add_argument("--log-file", type=str, default=None, help="Override path to blocked.log")

    args, unknown = parser.parse_known_args()

    log_path = get_log_path(args.log_file)
    cwd = args.cwd or os.getcwd()

    # CLI Direct Check Mode
    if args.check is not None:
        violation = check_command(args.check)
        if violation:
            rule, reason = violation
            block_and_exit(args.check, cwd, rule, reason, log_path)
        else:
            allow_and_exit(is_cli_check=True)

    # Claude Code Stdin IPC Mode
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            allow_and_exit()
        data = json.loads(raw_input)
    except Exception:
        # Non-JSON or empty stdin: fail open to avoid disrupting standard non-hook environments
        allow_and_exit()

    if not isinstance(data, dict):
        allow_and_exit()

    tool_name = str(data.get("tool_name", "")).strip().lower()
    # If not a Bash tool call, immediately pass through
    if tool_name != "bash":
        allow_and_exit()

    tool_input = data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        allow_and_exit()

    command = tool_input.get("command", "")
    if not isinstance(command, str) or not command.strip():
        allow_and_exit()

    project_cwd = data.get("cwd") or cwd

    violation = check_command(command)
    if violation:
        rule, reason = violation
        block_and_exit(command, project_cwd, rule, reason, log_path)
    else:
        allow_and_exit()


if __name__ == "__main__":
    main()
