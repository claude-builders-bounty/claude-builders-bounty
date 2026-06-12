#!/usr/bin/env python3
"""
pre-tool-use hook — Claude Code 安全钩子
拦截危险 bash 命令，防止误操作

安装:
  1. 创建目录: mkdir -p ~/.claude/hooks/
  2. 复制脚本: cp security_hook.py ~/.claude/hooks/pre-tool-use
  3. 添加权限: chmod +x ~/.claude/hooks/pre-tool-use

该钩子会拦截:
  - rm -rf (递归强制删除)
  - DROP TABLE (删除数据库表)
  - git push --force (强制推送)
  - TRUNCATE (清空表)
  - DELETE FROM 无 WHERE 子句 (危险删除)
"""

import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path

# ============ 配置 ============

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
HOOKS_DIR = os.path.expanduser("~/.claude/hooks")

# 危险命令模式：命令 -> 风险等级
DANGEROUS_PATTERNS = [
    {
        "pattern": r'\brm\s+(-rf|--recursive\s*--force|--force\s*--recursive)\b',
        "name": "rm -rf",
        "severity": "CRITICAL",
        "message": (
            "⛔ 危险命令被拦截: rm -rf\n\n"
            "原因: 递归强制删除文件，可能导致数据永久丢失。\n\n"
            "安全替代方案:\n"
            "  1. 使用 `trash` 命令代替（可恢复）\n"
            "  2. 明确指定目标: `rm -rf ./target-dir/`\n"
            "  3. 先用 `ls` 确认要删除的内容\n"
            "  4. 如果确实要执行，使用: `rm -rf /path/to/specific`\n"
            "\n如需放行，请确认目标路径后再执行。"
        ),
    },
    {
        "pattern": r'\bDROP\s+TABLE\b',
        "name": "DROP TABLE",
        "severity": "CRITICAL",
        "message": (
            "⛔ 危险命令被拦截: DROP TABLE\n\n"
            "原因: 删除数据库表将永久丢失数据。\n\n"
            "安全替代方案:\n"
            "  1. 先备份: `pg_dump -t tablename > backup.sql`\n"
            "  2. 使用 DROP TABLE IF EXISTS\n"
            "  3. 在事务中执行: BEGIN; DROP TABLE x; ROLLBACK;\n"
            "\n如需放行，请先确认已备份。"
        ),
    },
    {
        "pattern": r'\bgit\s+push\s+.*--force\b',
        "name": "git push --force",
        "severity": "HIGH",
        "message": (
            "⛔ 危险命令被拦截: git push --force\n\n"
            "原因: 强制推送会覆盖远程分支历史。\n\n"
            "安全替代方案:\n"
            "  1. 使用 `git push --force-with-lease`（更安全）\n"
            "  2. 确认没有其他人在该分支上工作\n"
            "  3. 先备份分支: `git branch backup-branch`\n"
            "\n如需放行，请确认不会影响协作者。"
        ),
    },
    {
        "pattern": r'\bTRUNCATE\b',
        "name": "TRUNCATE",
        "severity": "HIGH",
        "message": (
            "⛔ 危险命令被拦截: TRUNCATE\n\n"
            "原因: TRUNCATE 将清空整个表且不可回滚。\n\n"
            "安全替代方案:\n"
            "  1. 使用 DELETE FROM（可加 WHERE，支持事务）\n"
            "  2. 先备份数据\n"
            "  3. 在事务中执行\n"
            "\n如需放行，请确认已备份。"
        ),
    },
    {
        "pattern": r'\bDELETE\s+FROM\b(?!\s*\w+\s+WHERE\b)',
        "name": "DELETE FROM without WHERE",
        "severity": "HIGH",
        "message": (
            "⛔ 危险命令被拦截: DELETE FROM 无 WHERE 子句\n\n"
            "原因: 不带 WHERE 的 DELETE 会删除表中所有数据。\n\n"
            "安全替代方案:\n"
            "  1. 添加 WHERE 子句限定范围\n"
            "  2. 先用 SELECT 确认受影响的行数\n"
            "  3. 在事务中执行: BEGIN; DELETE; ROLLBACK;\n"
            "\n如需删除全部数据，请显式确认。"
        ),
    },
]

# 安全的白名单命令（包含以下路径的 rm -rf 被放行）
ALLOWED_RM_PATHS = [
    "node_modules",
    ".next",
    "dist",
    "build",
    ".cache",
    "__pycache__",
    ".git",
    "target",
    "venv",
    ".venv",
    "env",
]


def ensure_hooks_dir():
    """确保钩子目录存在"""
    Path(HOOKS_DIR).mkdir(parents=True, exist_ok=True)


def log_blocked(command, pattern_name, severity, project_path):
    """记录被拦截的命令到日志"""
    ensure_hooks_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "severity": severity,
        "pattern": pattern_name,
        "command": command,
        "project_path": project_path,
    }

    # 追加到日志文件
    log_line = (
        f"[{timestamp}] [{severity}] BLOCKED: {pattern_name}\n"
        f"  Command: {command}\n"
        f"  Project: {project_path}\n"
        f"  {'=' * 50}\n"
    )
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

    # 也保存为 JSON（便于程序读取）
    json_log = os.path.expanduser("~/.claude/hooks/blocked.json")
    try:
        if os.path.exists(json_log):
            with open(json_log, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = []
        history.append(log_entry)
        # 只保留最近 1000 条
        if len(history) > 1000:
            history = history[-1000:]
        with open(json_log, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    print(f"[HOOK] 📝 已记录到: {LOG_FILE}", file=sys.stderr)


def is_allowed_rm(command):
    """检查 rm -rf 是否在白名单路径"""
    for path in ALLOWED_RM_PATHS:
        if path in command:
            return True
    return False


def check_command(command, project_path):
    """
    检查命令是否危险
    返回: (is_dangerous, message)
    """
    if not command or not isinstance(command, str):
        return False, ""

    command_lower = command.lower().strip()

    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern["pattern"], command_lower, re.IGNORECASE):
            # rm -rf 特殊处理：检查路径白名单
            if pattern["name"] == "rm -rf" and is_allowed_rm(command):
                return False, ""

            log_blocked(command, pattern["name"], pattern["severity"], project_path)
            return True, pattern["message"]

    return False, ""


def main():
    """主入口：从 STDIN 读取命令进行检查"""
    import sys

    project_path = os.getcwd()

    # 读取传入的命令（Claude Code 将命令通过 stdin 传入）
    command_lines = sys.stdin.read() if not sys.stdin.isatty() else ""
    if not command_lines:
        # 从参数读取
        command_lines = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""

    if not command_lines:
        # 交互模式
        print("🔒 Claude Code 安全钩子已激活")
        print(f"📝 日志文件: {LOG_FILE}")
        print(f"📋 监控模式数: {len(DANGEROUS_PATTERNS)} 个危险模式")
        print("")
        print("输入要检查的命令（或直接按 Enter 退出）:")
        try:
            while True:
                cmd = input("> ").strip()
                if not cmd:
                    break
                is_danger, msg = check_command(cmd, project_path)
                if is_danger:
                    print(f"\n{msg}\n")
                    print(f"[HOOK] 命令已被拦截，已写入日志: {LOG_FILE}")
                else:
                    print("✅ 命令安全，可以通过")
        except (KeyboardInterrupt, EOFError):
            print()
        return

    for line in command_lines.split("\n"):
        line = line.strip()
        if line:
            is_danger, msg = check_command(line, project_path)
            if is_danger:
                print(msg, flush=True)
                sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
