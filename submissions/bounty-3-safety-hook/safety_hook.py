#!/usr/bin/env python3
"""
🛡️ Claude Code Safety Hook
阻止破坏性 bash 命令的执行
"""

import sys
import json
import re
from datetime import datetime
from pathlib import Path

class SafetyHook:
    """Claude Code pre-tool-use hook for blocking destructive commands"""
    
    # 危险的命令模式
    DANGEROUS_PATTERNS = [
        {
            "pattern": r"rm\s+-rf\s+/",
            "name": "rm -rf /",
            "severity": "CRITICAL",
            "description": "删除根目录，会摧毁整个系统"
        },
        {
            "pattern": r"rm\s+-rf\s+~",
            "name": "rm -rf ~",
            "severity": "CRITICAL",
            "description": "删除用户主目录"
        },
        {
            "pattern": r"rm\s+-rf\s+\.",
            "name": "rm -rf .",
            "severity": "CRITICAL",
            "description": "删除当前目录"
        },
        {
            "pattern": r"rm\s+-rf\s+\*",
            "name": "rm -rf *",
            "severity": "HIGH",
            "description": "递归强制删除所有文件"
        },
        {
            "pattern": r"DROP\s+TABLE",
            "name": "DROP TABLE",
            "severity": "HIGH",
            "description": "删除数据库表"
        },
        {
            "pattern": r"DROP\s+DATABASE",
            "name": "DROP DATABASE",
            "severity": "CRITICAL",
            "description": "删除整个数据库"
        },
        {
            "pattern": r"git\s+push\s+.*--force",
            "name": "git push --force",
            "severity": "HIGH",
            "description": "强制推送，会覆盖远程历史"
        },
        {
            "pattern": r"git\s+push\s+.*-f\b",
            "name": "git push -f",
            "severity": "HIGH",
            "description": "强制推送，会覆盖远程历史"
        },
        {
            "pattern": r"TRUNCATE\s+TABLE",
            "name": "TRUNCATE TABLE",
            "severity": "HIGH",
            "description": "清空表数据"
        },
        {
            "pattern": r"DELETE\s+FROM\s+\w+\s*$",
            "name": "DELETE FROM without WHERE",
            "severity": "HIGH",
            "description": "删除表中所有数据，没有 WHERE 条件"
        },
        {
            "pattern": r">\s*/\w+",
            "name": "Overwrite system file",
            "severity": "MEDIUM",
            "description": "重定向覆盖系统文件"
        },
        {
            "pattern": r"mkfs\.",
            "name": "mkfs",
            "severity": "CRITICAL",
            "description": "格式化文件系统"
        },
        {
            "pattern": r"dd\s+if=.*of=/dev/",
            "name": "dd to device",
            "severity": "CRITICAL",
            "description": "直接写入设备，可能破坏分区"
        }
    ]
    
    def __init__(self):
        self.log_file = Path.home() / ".claude" / "hooks" / "blocked.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def check_command(self, command: str) -> dict:
        """检查命令是否危险"""
        command = command.strip()
        
        for rule in self.DANGEROUS_PATTERNS:
            if re.search(rule["pattern"], command, re.IGNORECASE):
                return {
                    "blocked": True,
                    "rule": rule,
                    "command": command
                }
        
        return {"blocked": False}
    
    def log_blocked(self, result: dict, project_path: str = ""):
        """记录被阻止的命令"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": result["command"],
            "rule_name": result["rule"]["name"],
            "severity": result["rule"]["severity"],
            "project_path": project_path or "unknown"
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def format_block_message(self, result: dict) -> str:
        """格式化阻止消息"""
        rule = result["rule"]
        
        emoji = "🔴" if rule["severity"] == "CRITICAL" else "🟠" if rule["severity"] == "HIGH" else "🟡"
        
        message = f"""
{emoji} SAFETY HOOK BLOCKED THIS COMMAND

Command: {result["command"]}
Rule: {rule["name"]}
Severity: {rule["severity"]}

Why blocked:
{rule["description"]}

This command could cause irreversible damage to your system or data.
If you're sure you want to run it, you can:
1. Review the command carefully
2. Run it manually outside of Claude Code
3. Modify the command to be safer

Blocked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Logged to: {self.log_file}
"""
        return message
    
    def process(self, input_data: dict) -> dict:
        """处理 Claude Code hook 输入"""
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        
        # 只检查 bash 命令
        if tool_name != "bash":
            return {"allowed": True}
        
        command = tool_input.get("command", "")
        project_path = tool_input.get("project_path", "")
        
        # 检查命令
        result = self.check_command(command)
        
        if result["blocked"]:
            # 记录到日志
            self.log_blocked(result, project_path)
            
            # 返回阻止信息
            return {
                "allowed": False,
                "message": self.format_block_message(result)
            }
        
        return {"allowed": True}


def main():
    """主函数 - 从 stdin 读取 Claude Code hook 输入"""
    hook = SafetyHook()
    
    try:
        # 读取 JSON 输入
        input_data = json.load(sys.stdin)
        
        # 处理
        result = hook.process(input_data)
        
        # 输出结果
        print(json.dumps(result, indent=2))
        
        # 如果被阻止，以非零状态退出
        if not result.get("allowed", True):
            sys.exit(1)
            
    except json.JSONDecodeError as e:
        print(json.dumps({
            "allowed": False,
            "message": f"Invalid JSON input: {e}"
        }), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # 出错时允许执行（fail open）
        print(json.dumps({
            "allowed": True,
            "warning": f"Hook error: {e}"
        }))


if __name__ == "__main__":
    main()
