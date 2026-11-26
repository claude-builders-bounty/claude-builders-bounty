#!/usr/bin/env python3
"""把危险命令钩子装进 ~/.claude。

做的事：
  1. 复制 hooks/block_dangerous.py 到 ~/.claude/hooks/
  2. 在 ~/.claude/settings.json 里加一条 PreToolUse / Bash 的 hook 配置
     （已有配置会保留，原文件先备份成 settings.json.bak-<时间戳>）

用法：
  python3 install.py            # 正常安装
  python3 install.py --dry-run  # 只打印将要写入的内容
  python3 install.py --uninstall
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
HOOK_SRC = REPO_ROOT / "hooks" / "block_dangerous.py"
HOOK_NAME = "block_dangerous.py"


def claude_home() -> Path:
    """允许用 CLAUDE_HOME 覆盖，方便测试。"""
    override = os.environ.get("CLAUDE_HOME")
    return Path(override).expanduser() if override else Path.home() / ".claude"


def hook_command(hook_path: Path) -> str:
    return f"python3 {hook_path}"


def merge_settings(settings: dict, command: str) -> tuple[dict, bool]:
    hooks = settings.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])

    for entry in pre:
        if entry.get("matcher") != "Bash":
            continue
        for h in entry.get("hooks", []):
            if h.get("command") == command:
                return settings, False  # 已经装过

    target = None
    for entry in pre:
        if entry.get("matcher") == "Bash":
            target = entry
            break
    if target is None:
        target = {"matcher": "Bash", "hooks": []}
        pre.append(target)

    target.setdefault("hooks", []).append({"type": "command", "command": command})
    return settings, True


def remove_from_settings(settings: dict, command: str) -> tuple[dict, bool]:
    pre = settings.get("hooks", {}).get("PreToolUse", [])
    changed = False
    for entry in pre:
        hooks = entry.get("hooks", [])
        kept = [h for h in hooks if h.get("command") != command]
        if len(kept) != len(hooks):
            changed = True
            entry["hooks"] = kept
    settings["hooks"]["PreToolUse"] = [e for e in pre if e.get("hooks")]
    return settings, changed


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    uninstall = "--uninstall" in sys.argv

    home = claude_home()
    settings_path = home / "settings.json"
    hook_dst = home / "hooks" / HOOK_NAME
    command = hook_command(hook_dst)

    settings: dict = {}
    if settings_path.exists():
        raw = settings_path.read_text(encoding="utf-8").strip()
        settings = json.loads(raw) if raw else {}

    if uninstall:
        settings, changed = remove_from_settings(settings, command)
        if not dry_run and changed:
            shutil.copy2(settings_path, settings_path.with_suffix(".json.bak-" + datetime.now().strftime("%Y%m%d%H%M%S")))
            settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(("已移除" if changed else "本来就没装") + f"：{command}")
        return 0

    settings, added = merge_settings(settings, command)

    if dry_run:
        print("将要安装到:", hook_dst)
        print("settings.json 内容:")
        print(json.dumps(settings, indent=2, ensure_ascii=False))
        return 0

    hook_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HOOK_SRC, hook_dst)
    hook_dst.chmod(0o755)

    if settings_path.exists():
        backup = settings_path.with_name(
            "settings.json.bak-" + datetime.now().strftime("%Y%m%d%H%M%S"))
        shutil.copy2(settings_path, backup)
        print("已备份:", backup)

    settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"钩子已安装: {hook_dst}")
    print(f"配置已写入: {settings_path}（{'新增' if added else '原本就在'}）")
    print("重启 claude 会话后生效；试试让它跑 `rm -rf /tmp/should-block`。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
