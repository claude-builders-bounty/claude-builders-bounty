#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook
拦截危险 bash 命令，防止误操作导致数据丢失
"""

import json
import sys
import re
import os
from datetime import datetime
from pathlib import Path


# 危险命令模式列表（正则表达式）
DANGEROUS_PATTERNS = [
    # 删除类
    (r'\brm\s+(-\w*\s+)*-rf\b', 'rm -rf: 递归强制删除，不可恢复'),
    (r'\brm\s+(-\w*\s+)*-fr\b', 'rm -fr: 递归强制删除，不可恢复'),
    
    # 数据库危险操作
    (r'\bDROP\s+TABLE\b', 'DROP TABLE: 删除整张表，数据不可恢复'),
    (r'\bTRUNCATE\s+(TABLE\s+)?\w+', 'TRUNCATE: 清空表数据，不可恢复'),
    (r'\bDELETE\s+FROM\s+\w+\s*(?!WHERE\b)', 'DELETE 无 WHERE: 可能删除全表数据'),
    
    # Git 危险操作
    (r'\bgit\s+push\s+.*--force\b', 'git push --force: 可能覆盖远程提交历史'),
    (r'\bgit\s+push\s+.*-f\b', 'git push -f: 可能覆盖远程提交历史'),
]

# 日志路径
LOG_DIR = Path.home() / '.claude' / 'hooks'
LOG_FILE = LOG_DIR / 'blocked.log'


def ensure_log_dir():
    """确保日志目录存在"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_block(command: str, project_path: str, reason: str):
    """记录拦截事件"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"{timestamp} | {command} | {project_path} | {reason}\n"
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry)


def check_command(command: str) -> tuple[bool, str]:
    """
    检查命令是否危险
    返回: (是否安全, 拦截原因)
    """
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, reason
    return True, ""


def main():
    """主函数：处理 Claude Code hook 调用"""
    try:
        # 从 stdin 读取 JSON 输入
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # JSON 解析失败，放行
        print(json.dumps({"decision": "allow"}))
        return
    
    # 提取命令信息
    tool_name = input_data.get('tool_name', '')
    tool_input = input_data.get('tool_input', {})
    command = tool_input.get('command', '')
    project_path = input_data.get('project_path', os.getcwd())
    
    # 只拦截 bash 命令
    if tool_name != 'bash' or not command:
        print(json.dumps({"decision": "allow"}))
        return
    
    # 检查命令是否安全
    is_safe, reason = check_command(command)
    
    if is_safe:
        # 安全，放行
        print(json.dumps({"decision": "allow"}))
    else:
        # 危险命令，拦截并记录
        ensure_log_dir()
        log_block(command, project_path, reason)
        
        # 返回阻止消息给 Claude
        response = {
            "decision": "block",
            "reason": f"⚠️ 命令被拦截: {reason}\n\n"
                     f"被拦截的命令: {command}\n"
                     f"日志已记录到: {LOG_FILE}\n\n"
                     f"如需执行此命令，请手动运行。"
        }
        print(json.dumps(response))


if __name__ == '__main__':
    main()
