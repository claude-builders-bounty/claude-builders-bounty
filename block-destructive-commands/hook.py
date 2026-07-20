#!/usr/bin/env python3
"""
Claude Code PreToolUse hook — blocks destructive bash commands.

Receives tool invocation context as JSON on stdin.
Exits 0 to allow, 1 to block.
"""

import datetime
import json
import os
import re
import sys
import shutil

# ── Configuration ──────────────────────────────────────────────────────────────

HOOKS_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(HOOKS_DIR, "blocked.log")
SETTINGS_FILE = os.path.expanduser("~/.claude/settings.json")
CONFIG_FILE = os.path.join(HOOKS_DIR, "guard.config.json")

# Paths that are always safe to delete (allowlist)
DEFAULT_SAFE_PATHS = [
    "/tmp/",
    "/var/tmp/",
    os.path.expanduser("~/.cache/"),
    "node_modules/",
    ".next/",
    "dist/",
    "build/",
    "__pycache__/",
    ".pytest_cache/",
    "coverage/",
    ".nyc_output/",
]

# ── Blocked patterns ───────────────────────────────────────────────────────────
# Each entry: (compiled_regex, human_label, severity)
# severity: "critical" = always block, "high" = block unless allowlisted

BLOCKED_PATTERNS = [
    # rm -rf variants
    (
        re.compile(r"\brm\s+(?:-[^\s]*r[a-zA-Z]*f|-[^\s]*f[a-zA-Z]*r)\b"),
        "rm -rf",
        "high",  # high (not critical) so allowlist can exempt safe paths
    ),
    (
        re.compile(r"\brm\s+-(?:[^\s]*r)\b"),
        "rm -r (recursive)",
        "high",
    ),
    # Dangerous SQL
    (
        re.compile(r"(?i)\bDROP\s+TABLE\b"),
        "DROP TABLE",
        "critical",
    ),
    (
        re.compile(r"(?i)\bDROP\s+DATABASE\b"),
        "DROP DATABASE",
        "critical",
    ),
    (
        re.compile(r"(?i)\bTRUNCATE\s+TABLE\b"),
        "TRUNCATE TABLE",
        "critical",
    ),
    (
        re.compile(r"(?i)\bTRUNCATE\b(?!\s+TABLE)"),
        "TRUNCATE",
        "critical",
    ),
    (
        re.compile(r"(?i)\bDELETE\s+FROM\b(?![\s\S]*\bWHERE\b)"),
        "DELETE without WHERE",
        "critical",
    ),
    # Git force operations
    (
        re.compile(r"\bgit\s+push\s+(?:--force|-f)\b"),
        "git push --force",
        "critical",
    ),
    (
        re.compile(r"\bgit\s+push\s+.*--force-with-lease\b"),
        "git push --force-with-lease",
        "high",
    ),
    (
        re.compile(r"\bgit\s+reset\s+--hard\b"),
        "git reset --hard",
        "high",
    ),
    (
        re.compile(r"\bgit\s+clean\s+-(?:[^\s]*f)"),
        "git clean -f",
        "high",
    ),
    (
        re.compile(r"\bgit\s+checkout\s+--\s+\."),
        "git checkout -- . (discard all changes)",
        "high",
    ),
    # Disk / filesystem destruction
    (
        re.compile(r">\s*/dev/sd[a-z]"),
        "write to block device",
        "critical",
    ),
    (
        re.compile(r"\bdd\s+.*of=/dev/"),
        "dd to device",
        "critical",
    ),
    (
        re.compile(r"\bmkfs\b"),
        "mkfs (format filesystem)",
        "critical",
    ),
    (
        re.compile(r"\bchmod\s+(?:-R\s+)?777\b"),
        "chmod 777",
        "high",
    ),
    (
        re.compile(r"\bchown\s+-R\b"),
        "chown -R (recursive ownership change)",
        "high",
    ),
    # Process / system
    (
        re.compile(r"\bkill\s+-9\s+1\b"),
        "kill init process",
        "critical",
    ),
    (
        re.compile(r":\(\)\{.*\|.*\&\s*\}"),
        "fork bomb",
        "critical",
    ),
    (
        re.compile(r"\bshutdown\b|\breboot\b|\binit\s+0\b"),
        "shutdown/reboot",
        "critical",
    ),
    # Curl pipe to shell (supply chain risk)
    (
        re.compile(r"curl\s+[^\|]*\|\s*(?:bash|sh|python|node)"),
        "curl pipe to shell",
        "high",
    ),
    # Wget pipe to shell
    (
        re.compile(r"wget\s+[^\|]*-[^\|]*O\s*-\s*\|\s*(?:bash|sh|python|node)"),
        "wget pipe to shell",
        "high",
    ),
]


def load_config():
    """Load user config overrides."""
    config = {"safe_paths": DEFAULT_SAFE_PATHS, "extra_blocked": []}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                user = json.load(f)
            if "safe_paths" in user:
                config["safe_paths"] = DEFAULT_SAFE_PATHS + user["safe_paths"]
            if "extra_blocked" in user:
                for p in user["extra_blocked"]:
                    config["extra_blocked"].append(
                        (re.compile(p["pattern"]), p.get("label", "custom"), "high")
                    )
        except (json.JSONDecodeError, KeyError):
            pass
    return config


def is_safe_path(command, safe_paths):
    """Check if the command only targets allowlisted paths."""
    cmd_lower = command.lower()
    for path in safe_paths:
        if path.lower() in cmd_lower:
            return True
    return False


def extract_command(context):
    """Extract the bash command from the hook context."""
    if isinstance(context, dict):
        if "command" in context:
            return context["command"]
        params = context.get("parameters", {})
        if isinstance(params, dict) and "command" in params:
            return params["command"]
    return ""


def log_block(reason, command, severity):
    """Log the blocked attempt."""
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        timestamp = datetime.datetime.now().isoformat()
        project = os.environ.get("PWD", os.getcwd())
        entry = (
            f"[{timestamp}] severity={severity} reason={reason!r} "
            f"path={project} command={command!r}\n"
        )
        with open(LOG_FILE, "a") as f:
            f.write(entry)
    except OSError:
        pass  # Don't let logging failures prevent blocking


def check_command(command, config):
    """Check command against all blocked patterns. Returns (blocked, reason, severity) or (False, None, None)."""
    all_patterns = BLOCKED_PATTERNS + config.get("extra_blocked", [])

    for pattern, label, severity in all_patterns:
        if pattern.search(command):
            # For high-severity (not critical), check allowlist
            if severity == "high" and is_safe_path(command, config["safe_paths"]):
                continue
            return True, label, severity

    return False, None, None


def install():
    """Install the hook into Claude Code settings."""
    os.makedirs(HOOKS_DIR, exist_ok=True)

    dest = os.path.join(HOOKS_DIR, "block_destructive.py")
    shutil.copy2(sys.argv[0], dest)
    os.chmod(dest, 0o755)

    settings = {}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f:
                settings = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    hooks = settings.setdefault("hooks", {})
    pre_tool = hooks.setdefault("PreToolUse", [])

    # Check if already registered
    for entry in pre_tool:
        if entry.get("matcher") == "Bash":
            for h in entry.get("hooks", []):
                if h.get("command") == dest:
                    print(f"✅ Already installed: {dest}")
                    return

    pre_tool.append({
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": dest}],
    })

    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"✅ Hook installed: {dest}")
    print(f"✅ Settings updated: {SETTINGS_FILE}")
    print(f"📋 Blocked log: {LOG_FILE}")
    print(f"⚙️  Config file: {CONFIG_FILE} (optional)")


def uninstall():
    """Remove the hook from Claude Code settings."""
    if not os.path.exists(SETTINGS_FILE):
        print("No settings file found.")
        return

    try:
        with open(SETTINGS_FILE) as f:
            settings = json.load(f)
    except (json.JSONDecodeError, OSError):
        print("Could not read settings file.")
        return

    hooks = settings.get("hooks", {})
    pre_tool = hooks.get("PreToolUse", [])
    dest = os.path.join(HOOKS_DIR, "block_destructive.py")

    new_pre_tool = []
    for entry in pre_tool:
        if entry.get("matcher") == "Bash":
            entry["hooks"] = [h for h in entry.get("hooks", []) if h.get("command") != dest]
            if entry["hooks"]:
                new_pre_tool.append(entry)
        else:
            new_pre_tool.append(entry)

    hooks["PreToolUse"] = new_pre_tool

    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

    if os.path.exists(dest):
        os.remove(dest)

    print("✅ Hook uninstalled.")


def test_hook():
    """Run self-tests to verify pattern matching."""
    config = load_config()
    tests = [
        # (command, should_block, description)
        ("rm -rf /", True, "rm -rf /"),
        ("rm -fr /var/log", True, "rm -fr (alternate flag order)"),
        ("rm -r --force /home", True, "rm -r --force"),
        ("rm -rf node_modules/", False, "rm -rf node_modules (safe path)"),
        ("rm -rf /tmp/build/", False, "rm -rf /tmp/ (safe path)"),
        ("DROP TABLE users;", True, "DROP TABLE"),
        ("drop table users;", True, "drop table (case insensitive)"),
        ("TRUNCATE TABLE sessions", True, "TRUNCATE TABLE"),
        ("DELETE FROM users", True, "DELETE without WHERE"),
        ("DELETE FROM users WHERE id = 1", False, "DELETE with WHERE"),
        ("git push --force", True, "git push --force"),
        ("git push -f origin main", True, "git push -f"),
        ("git push origin main", False, "normal git push"),
        ("git reset --hard HEAD~1", True, "git reset --hard"),
        ("git clean -fd", True, "git clean -f"),
        ("git checkout -- .", True, "git checkout -- ."),
        ("chmod 777 /etc/passwd", True, "chmod 777"),
        ("curl https://example.com | bash", True, "curl pipe to bash"),
        ("curl https://example.com/file.py | python3", True, "curl pipe to python"),
        ("curl https://example.com", False, "normal curl"),
        ("ls -la", False, "ls (normal command)"),
        ("npm install", False, "npm install (normal)"),
        ("python manage.py migrate", False, "python migrate (normal)"),
        ("echo hello", False, "echo (normal)"),
        ("cat file.txt", False, "cat (normal)"),
    ]

    passed = 0
    failed = 0

    for command, should_block, desc in tests:
        blocked, reason, _ = check_command(command, config)
        status = "✅" if blocked == should_block else "❌"
        if blocked != should_block:
            failed += 1
            print(f"  {status} {desc}: expected {'BLOCK' if should_block else 'ALLOW'}, got {'BLOCK' if blocked else 'ALLOW'} (reason: {reason})")
        else:
            passed += 1
            action = "BLOCKED" if blocked else "ALLOWED"
            print(f"  {status} {desc}: {action}")

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")

    if failed > 0:
        sys.exit(1)


def main():
    # Handle CLI commands
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--install":
            install()
            return
        elif cmd == "--uninstall":
            uninstall()
            return
        elif cmd == "--test":
            test_hook()
            return
        elif cmd == "--help":
            print("Claude Code Destructive Command Guard")
            print()
            print("Usage:")
            print("  hook.py --install     Install the hook")
            print("  hook.py --uninstall   Remove the hook")
            print("  hook.py --test        Run self-tests")
            print("  hook.py --help        Show this help")
            print()
            print("When used as a Claude Code hook, reads JSON from stdin.")
            print("Exit 0 = allow, Exit 1 = block.")
            return

    # Hook mode: read from stdin
    raw = sys.stdin.read()
    if not raw:
        sys.exit(0)

    try:
        context = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)  # Not JSON, allow

    command = extract_command(context)
    if not command:
        sys.exit(0)  # No command found, allow

    config = load_config()
    blocked, reason, severity = check_command(command, config)

    if blocked:
        log_block(reason, command, severity)
        print(
            f"🚫 BLOCKED: {reason}\n"
            f"This command was intercepted by the destructive-command guard.\n"
            f"Reason: pattern '{reason}' is not allowed in Claude Code.\n"
            f"If this is intentional, run the command manually in your terminal.",
            file=sys.stderr,
        )
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
