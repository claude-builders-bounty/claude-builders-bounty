#!/usr/bin/env python3
from __future__ import annotations

import shutil
import stat
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HOOK_NAME = "destructive-command-guard.py"
TARGET_DIR = Path.home() / ".claude" / "hooks"
TARGET = TARGET_DIR / HOOK_NAME


def main() -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / HOOK_NAME, TARGET)
    TARGET.chmod(TARGET.stat().st_mode | stat.S_IXUSR)

    print(f"Installed {TARGET}")
    print()
    print("Add hooks/settings.example.json to your Claude Code settings, or use:")
    print()
    print('{')
    print('  "hooks": {')
    print('    "PreToolUse": [')
    print('      {')
    print('        "matcher": "Bash",')
    print('        "hooks": [')
    print('          {')
    print('            "type": "command",')
    print(f'            "command": "python3 {TARGET}"')
    print('          }')
    print('        ]')
    print('      }')
    print('    ]')
    print('  }')
    print('}')


if __name__ == "__main__":
    main()
