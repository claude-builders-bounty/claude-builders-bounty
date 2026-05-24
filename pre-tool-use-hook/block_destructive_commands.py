#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: Block destructive bash commands.

This hook intercepts Bash tool invocations and blocks dangerous commands
that could cause data loss or system damage while allowing safe variants.

Install:
    mkdir -p ~/.claude/hooks/
    cp block_destructive_commands.py ~/.claude/hooks/pre-tool-use

Input (stdin):  JSON: {"tool_use_id":"...","tool_name":"Bash","tool_input":{"command":"..."}}
Output (stdout): JSON: {"is_allowed": true} or {"is_allowed": false, "suggestion": "...", "confidence": 1.0}
"""

import json
import re
import sys


def _re(pattern: str) -> re.Pattern:
    """Compile a regex with IGNORECASE | VERBOSE (strips leading whitespace from each line)."""
    return re.compile(pattern.strip(), re.IGNORECASE | re.VERBOSE)


# ── Danger patterns: (regex, suggestion) ──

DANGER_PATTERNS: list[tuple[re.Pattern, str]] = [

    # ── rm -rf / (root wipe, all flag variants) ──
    (
        _re(r'''
            \b rm \s+
            (?: -{1,2} [a-zA-Z]* [rRfFvV] [a-zA-Z]* \s+ )*
            (?: -- \s+ )?
            /
            (?= \s | $ | [;&|] )
        '''),
        "Blocked: 'rm -rf /' would delete the entire filesystem. "
        "Use 'rm -rf ./TARGET' or 'rm -rf /tmp/TARGET' instead."
    ),
    (
        _re(r'''
            \b sudo \s+ rm \s+
            (?: -{1,2} [a-zA-Z]* [rRfFvV] [a-zA-Z]* \s+ )*
            (?: -- \s+ )?
            /
            (?= \s | $ | [;&|] )
        '''),
        "Blocked: 'sudo rm -rf /' would delete the entire filesystem with elevated privileges. "
        "Use 'rm -rf ./TARGET' or 'rm -rf /tmp/TARGET' instead."
    ),
    # rm on critical system directories
    (
        _re(r'''
            \b rm \s+
            (?: -{1,2} [a-zA-Z]* [rRfFvV] [a-zA-Z]* \s+ )*
            (?: -- \s+ )?
            / (?: [^\s]* / )? (boot|etc|lib|lib64|bin|sbin|usr|var|proc|sys|dev)
            (?: / | [?*] | \s | $ )
        '''),
        "Blocked: Deleting critical system directories (/boot, /etc, /lib, /bin, /usr, /var, /proc, /sys, /dev) would break the OS."
    ),

    # ── dd writing to a block device ──
    (
        _re(r'\b dd \b [^;]* of \s* = \s* /dev/sd [a-z]'),
        "Blocked: 'dd ... of=/dev/sdX' writes directly to a block device, which can destroy the disk."
    ),
    (
        _re(r'\b dd \b [^;]* of \s* = \s* /dev/nvme [0-9]'),
        "Blocked: 'dd ... of=/dev/nvmeX' writes directly to an NVMe device, which can destroy the disk."
    ),

    # ── Fork bombs ──
    (
        _re(r'[:\$] \s* \( \s* \) \s* \{'),
        "Blocked: Detected a fork bomb pattern (':(){ :|:& };:'). This would crash the system by exhausting processes."
    ),
    (
        _re(r'\b \w+ \(\) \s* \{ .* \| .* & \s* \}'),
        "Blocked: Detected a fork bomb variant. This would crash the system by spawning infinite processes."
    ),
    (
        _re(r'\{ \s* \| : \| : \& \s* \}'),
        "Blocked: Detected a fork bomb variant. This would crash the system."
    ),

    # ── > /dev/sda (direct write via redirect) ──
    (
        _re(r'(?: ^ | [;&|] ) \s* > \s* /dev/sd [a-z]'),
        "Blocked: Writing directly to a block device (> /dev/sdX) would destroy the disk partition table."
    ),
    (
        _re(r'(?: ^ | [;&|] ) \s* > \s* /dev/nvme [0-9]'),
        "Blocked: Writing directly to a block device (> /dev/nvmeX) would destroy the disk."
    ),

    # ── chmod -R 000 / (permission nuke) ──
    (
        _re(r'\b chmod \s+ (?: -{1,2} [a-zA-Z]* R [a-zA-Z]* \s+ )? 0{3,4} \s+ /'),
        "Blocked: 'chmod -R 000 /' would remove all read/execute permissions on the system, making it unbootable."
    ),

    # ── mv /* to /dev/null ──
    (
        _re(r'\b mv \s+ /\* \s+ /dev/null'),
        "Blocked: 'mv /* /dev/null' would move all root files to /dev/null, deleting the OS."
    ),
    (
        _re(r'\b mv \s+ /\w+ \s+ /dev/null'),
        "Blocked: Moving system directories to /dev/null destroys the OS."
    ),

    # ── Shutdown / reboot / poweroff / init ──
    (
        _re(r'\b shutdown \s+ (?: -[a-z]+ \s+ )? (?: now | \+0 | \+ \s* 0 )'),
        "Blocked: 'shutdown now' would terminate the session. Use a graceful shutdown instead if intended."
    ),
    (
        _re(r'\b reboot \s* (?: -[fp] | --force )? \s* $'),
        "Blocked: 'reboot' would restart the system. If you need to restart, please confirm first."
    ),
    (
        _re(r'\b poweroff \s* $'),
        "Blocked: 'poweroff' would shut down the system."
    ),
    (
        _re(r'\b init \s+ 0 \b'),
        "Blocked: 'init 0' would shut down the system."
    ),
    (
        _re(r'\b init \s+ 6 \b'),
        "Blocked: 'init 6' would reboot the system."
    ),

    # ── mkfs on block device / format ──
    (
        _re(r'\b mkfs \. [a-z0-9]+ \s+ /dev/sd [a-z]'),
        "Blocked: 'mkfs' on a block device would format (erase) the filesystem, causing data loss."
    ),
    (
        _re(r'\b mkfs \. [a-z0-9]+ \s+ /dev/nvme [0-9]'),
        "Blocked: 'mkfs' on an NVMe device would format (erase) the filesystem."
    ),
    (
        _re(r'\b format \s+ [a-zA-Z]: \\\\?'),
        "Blocked: 'format' on a Windows drive would erase the entire drive."
    ),

    # ── curl / wget pipe to bash ──
    (
        _re(r'(?: curl | wget ) \s+ (?: -s [a-z]* )? \s+ \S+ \s* \| \s* bash'),
        "Caution: Piping a remote script directly into bash (curl ... | bash) is dangerous. Verify the source first."
    ),

    # ── cat block device ──
    (
        _re(r'\b cat \s+ /dev/sd [a-z]'),
        "Blocked: 'cat /dev/sdX' could cause a terminal to interpret binary data and possibly crash."
    ),

    # ── chown recursion on root ──
    (
        _re(r'\b chown \s+ (?: -{1,2} [a-zA-Z]* R [a-zA-Z]* \s+ )? [a-z_] [a-z0-9_.-]* (?: : [a-z_] [a-z0-9_.-]* )? \s+ /'),
        "Blocked: Recursive 'chown' on '/' would change ownership of the entire filesystem."
    ),
]


# ── Whitelist: safe variants that look dangerous ──

ALLOWLIST_PATTERNS: list[re.Pattern] = [
    # rm -rf ./...  (relative path)
    _re(r'\b rm \s+ (?: -{1,2} [a-zA-Z]* [rRfFvV] [a-zA-Z]* \s+ )* \.'),
    # rm -rf /tmp/...
    _re(r'\b rm \s+ (?: -{1,2} [a-zA-Z]* [rRfFvV] [a-zA-Z]* \s+ )* /tmp'),
    # rm -rf /var/tmp/...
    _re(r'\b rm \s+ (?: -{1,2} [a-zA-Z]* [rRfFvV] [a-zA-Z]* \s+ )* /var/tmp'),
    # dd with of= starting with ./ or a letter (writing to a regular file)
    _re(r'\b dd \b [^;]* of \s* = \s* \.'),
    _re(r'\b dd \b [^;]* of \s* = \s* [a-zA-Z] (?! /dev/ )'),
    # mkfs on a regular file (.img, .bin, .ext*)
    _re(r'\b mkfs \. [a-z0-9]+ \s+ \S+ \. (?: img | bin | ext\d )'),
    _re(r'\b mkfs \s+ -t \s+ \S+ \s+ \S+ \. (?: img | bin | ext\d )'),
    # mkfs --help
    _re(r'\b mkfs \s+ (?: -h | --help )'),
]


def is_command_allowed(command: str) -> tuple[bool, str | None]:
    """
    Check if a bash command is allowed.

    Returns:
        (True, None) if allowed
        (False, suggestion) if blocked
    """
    # Whitelist first (safe variants of dangerous commands)
    for pattern in ALLOWLIST_PATTERNS:
        if pattern.search(command):
            return True, None

    # Then check danger patterns
    for pattern, suggestion in DANGER_PATTERNS:
        if pattern.search(command):
            return False, suggestion

    return True, None


def main() -> None:
    """Read JSON from stdin, check command, write JSON result to stdout."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            json.dump({"is_allowed": True}, sys.stdout, ensure_ascii=False)
            sys.stdout.flush()
            return

        data = json.loads(raw)

        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})

        # Only intercept Bash tool calls
        if tool_name in ("Bash", "BashCode"):
            command = (tool_input.get("command", "")
                       or tool_input.get("code", ""))
        else:
            json.dump({"is_allowed": True}, sys.stdout, ensure_ascii=False)
            sys.stdout.flush()
            return

        if not command:
            json.dump({"is_allowed": True}, sys.stdout, ensure_ascii=False)
            sys.stdout.flush()
            return

        allowed, suggestion = is_command_allowed(command)

        if allowed:
            json.dump({"is_allowed": True}, sys.stdout, ensure_ascii=False)
        else:
            json.dump({
                "is_allowed": False,
                "suggestion": suggestion,
                "confidence": 1.0,
            }, sys.stdout, ensure_ascii=False)

        sys.stdout.flush()

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        json.dump({"is_allowed": True}, sys.stdout, ensure_ascii=False)
        sys.stdout.flush()
    except Exception as e:
        print(f"Error: Unexpected error in block_destructive_commands hook: {e}", file=sys.stderr)
        json.dump({"is_allowed": True}, sys.stdout, ensure_ascii=False)
        sys.stdout.flush()


if __name__ == "__main__":
    main()
