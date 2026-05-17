#!/usr/bin/env python3
"""
🛡️ claude-guard — Pre-tool-use hook for Claude Code
Intercepts dangerous bash commands before execution.
Install: cp this file to ~/.claude/hooks/pre-tool-use
"""

import os
import sys
import json
import datetime
import re
from pathlib import Path

HOOK_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

DANGEROUS_PATTERNS = [
    # 文件系统破坏
    (r'\brm\s+-rf\b', "❌ Blocked: `rm -rf` — permanent file deletion. Use `trash` or target specific files."),
    
    # Git强制推送
    (r'git\s+push\s+.*--force', "❌ Blocked: `git push --force` — destroys remote history. Use `git push --force-with-lease` instead."),
    
    # 数据库操作
    (r'\bDROP\s+TABLE\b', "❌ Blocked: `DROP TABLE` — irreversible data loss."),
    (r'\bTRUNCATE\b', "❌ Blocked: `TRUNCATE` — destroys all rows. Use `DELETE` with a WHERE clause."),
    (r'\bDELETE\s+FROM\b(?!\s*\()(?![^;]*\s+WHERE\s)', "❌ Blocked: `DELETE FROM` without WHERE clause — would delete all rows."),
    
    # 直接数据库文件操作
    (r'\brm\s+.*\.(db|sqlite|sqlite3)\b', "❌ Blocked: deleting database files directly."),
    
    # 系统破坏
    (r'\bsudo\s+rm\b', "❌ Blocked: `sudo rm` — escalated destructive command."),
    (r'\bmkfs\.', "❌ Blocked: filesystem formatting command."),
    (r'\bdd\s+if=', "❌ Blocked: `dd` with input file — potential disk overwrite."),
    
    # 批量kill
    (r'\bkill\s+-9\b', "⚠️ Warning: `kill -9` — forceful process termination."),
]

def check_command(tool_name: str, args: list) -> dict:
    """检查命令是否危险"""
    cmd_str = " ".join(args).lower() if args else ""
    
    for pattern, message in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd_str, re.IGNORECASE):
            # 记录日志
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "command": cmd_str,
                "tool": tool_name,
                "project": os.getcwd(),
                "reason": message,
            }
            
            HOOK_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(HOOK_LOG, "a") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
            return {
                "block": True,
                "message": f"{message}\n\n📝 This attempt has been logged to {HOOK_LOG}",
            }
    
    return {"block": False}


def main():
    """主入口：从环境变量读取Claude Code传入的参数"""
    # Claude Code hooks通过环境变量传递工具调用信息
    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
    tool_args_raw = os.environ.get("CLAUDE_TOOL_ARGS", "[]")
    
    try:
        tool_args = json.loads(tool_args_raw) if tool_args_raw else []
    except json.JSONDecodeError:
        tool_args = []
    
    # 只拦截bash工具
    if tool_name in ("bash", "execute_command", "run"):
        result = check_command(tool_name, tool_args)
        if result["block"]:
            print(json.dumps(result))
            sys.exit(1)
    
    # 默认放行
    sys.exit(0)


if __name__ == "__main__":
    main()
