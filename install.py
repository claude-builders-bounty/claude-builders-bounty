#!/usr/bin/env python3
"""
1-Command Installer for Claude Code Destructive Bash Command Interceptor Hook.

Installs:
1. .claude/hooks/block_destructive.py -> ~/.claude/hooks/block_destructive.py
2. Registers PreToolUse hook configuration in ~/.claude/settings.json

Usage:
  python install.py
  python install.py --dry-run
  python install.py --target-dir /path/to/.claude
"""

import sys
import os
import shutil
import json
import argparse
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Install Claude Code Destructive Command Prevention Hook"
    )
    parser.add_argument(
        "--target-dir",
        type=str,
        default=None,
        help="Target Claude configuration directory (default: ~/.claude)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate installation without modifying filesystem"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing hook files"
    )
    return parser.parse_args()


def install():
    args = parse_args()
    repo_root = Path(__file__).resolve().parent
    source_hook = repo_root / ".claude" / "hooks" / "block_destructive.py"

    if not source_hook.exists():
        sys.stderr.write(f"Error: Source hook script not found at {source_hook}\n")
        sys.exit(1)

    claude_dir = Path(args.target_dir) if args.target_dir else Path.home() / ".claude"
    hooks_dir = claude_dir / "hooks"
    target_hook = hooks_dir / "block_destructive.py"
    settings_file = claude_dir / "settings.json"

    print("==================================================")
    print(" Claude Code Destructive Command Hook Installer")
    print("==================================================")
    print(f"Source Hook:   {source_hook}")
    print(f"Target Hook:   {target_hook}")
    print(f"Settings File: {settings_file}")
    if args.dry_run:
        print("[MODE: DRY RUN - No files will be modified]")
    print()

    # Step 1: Copy hook file
    if not args.dry_run:
        hooks_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_hook, target_hook)
        # Set executable permissions on POSIX
        if os.name == "posix":
            try:
                target_hook.chmod(target_hook.stat().st_mode | 0o755)
            except Exception:
                pass
        print(f"[OK] Installed hook to {target_hook}")
    else:
        print(f"[DRY-RUN] Would copy {source_hook} -> {target_hook}")

    # Step 2: Configure settings.json
    settings = {}
    if settings_file.exists():
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to parse existing {settings_file}: {e}. Creating new.")
            settings = {}

    hooks_config = settings.setdefault("hooks", {})
    pre_tool_hooks = hooks_config.setdefault("PreToolUse", [])

    # Command invocation string
    hook_command = "python ~/.claude/hooks/block_destructive.py"

    # Check if already registered
    already_registered = False
    for entry in pre_tool_hooks:
        if isinstance(entry, dict) and entry.get("matcher", "").lower() == "bash":
            inner_hooks = entry.get("hooks", [])
            for h in inner_hooks:
                if isinstance(h, dict) and "block_destructive.py" in h.get("command", ""):
                    already_registered = True
                    break

    if already_registered:
        print("[INFO] PreToolUse hook is already configured in settings.json")
    else:
        bash_entry = None
        for entry in pre_tool_hooks:
            if isinstance(entry, dict) and entry.get("matcher", "").lower() == "bash":
                bash_entry = entry
                break

        hook_item = {
            "type": "command",
            "command": hook_command
        }

        if bash_entry is not None:
            bash_entry.setdefault("hooks", []).append(hook_item)
        else:
            pre_tool_hooks.append({
                "matcher": "Bash",
                "hooks": [hook_item]
            })

        if not args.dry_run:
            claude_dir.mkdir(parents=True, exist_ok=True)
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
            print(f"[OK] Registered hook in {settings_file}")
        else:
            print(f"[DRY-RUN] Would register PreToolUse hook in {settings_file}")

    print("\n[SUCCESS] Installation complete. Claude Code is now protected against destructive bash commands.")
    print("Blocked attempts will be recorded in ~/.claude/hooks/blocked.log")
    return 0


if __name__ == "__main__":
    sys.exit(install())
