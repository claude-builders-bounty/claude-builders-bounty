#!/usr/bin/env python3
"""Idempotently register destructor_guard.py as a PreToolUse (Bash) hook in
~/.claude/settings.json. Safe to re-run: it never duplicates an existing entry
and never touches unrelated hook configuration."""
import json
import os
import sys

SETTINGS = os.path.expanduser("~/.claude/settings.json")
HOOK_PATH = os.path.expanduser("~/.claude/destructor_guard.py")


def main():
    if not os.path.exists(HOOK_PATH):
        sys.stderr.write(
            "error: %s not found. Run install step 1 (download the hook) first.\n" % HOOK_PATH
        )
        sys.exit(1)

    cfg = {}
    if os.path.exists(SETTINGS):
        with open(SETTINGS) as f:
            try:
                cfg = json.load(f)
            except ValueError:
                cfg = {}
        if not isinstance(cfg, dict):
            cfg = {}

    cmd_line = "python3 %s" % HOOK_PATH
    hooks_cfg = cfg.setdefault("hooks", {})
    if not isinstance(hooks_cfg, dict):
        hooks_cfg = {}
        cfg["hooks"] = hooks_cfg
    pre = hooks_cfg.setdefault("PreToolUse", [])
    if not isinstance(pre, list):
        pre = []
        hooks_cfg["PreToolUse"] = pre

    for existing in pre:
        for h in existing.get("hooks", []) if isinstance(existing, dict) else []:
            if "destructor_guard" in str(h.get("command", "")):
                print("destructor-guard already registered - nothing to do.")
                return

    new_entry = {
        "type": "command",
        "command": cmd_line,
        "timeout": 10,
    }
    for existing in pre:
        if isinstance(existing, dict) and existing.get("matcher") == "Bash":
            existing.setdefault("hooks", []).append(new_entry)
            break
    else:
        pre.append({"matcher": "Bash", "hooks": [new_entry]})

    os.makedirs(os.path.dirname(SETTINGS), exist_ok=True)
    with open(SETTINGS, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    print("destructor-guard registered in %s" % SETTINGS)


if __name__ == "__main__":
    main()
