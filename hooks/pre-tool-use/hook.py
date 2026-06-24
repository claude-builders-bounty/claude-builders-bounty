#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook — 拦截危险 bash 命令。

安装: ln -sf $(pwd)/hook.py ~/.claude/hooks/pre-tool-use
"""

import json
import os
import re
import sys
import time
from pathlib import Path

# ── 危险模式定义 ──────────────────────────────────────────────
# 每条规则: (正则, 危险等级, 说明)
BLOCKED_PATTERNS = [
    # 毁灭性文件操作
    (r'\brm\s+(-rf|--recursive\b.*-f?|-[rR]?[fF]?.*-[fF]?[rR]?)', 'CRITICAL', 'rm -rf 会永久删除文件'),
    (r'\brm\b.*\s+/\s*$',                           'CRITICAL', '删除根目录 /'),

    # 数据库破坏
    (r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b',         'CRITICAL', 'DROP 会永久删除数据库对象'),
    (r'\bTRUNCATE\b',                                'HIGH',     'TRUNCATE 会清空整张表'),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)',            'HIGH',     'DELETE 没有 WHERE 子句——会清空整张表'),

    # Git 破坏
    (r'\bgit\s+push\s+(--force|--force-with-lease)\b', 'CRITICAL', 'force push 会覆盖远程历史'),
    (r'\bgit\s+reset\s+(--hard|--merge)\b',          'HIGH',     'git reset --hard 会丢弃未提交的更改'),
    (r'\bgit\s+rebase\s+--(onto|interactive)\b',     'MEDIUM',   'rebase 会改写提交历史'),

    # 危险 shell
    (r'\beval\b',                                    'HIGH',     'eval 执行字符串命令——易被注入'),
    (r'\bexec\b',                                    'MEDIUM',   'exec 替换当前进程'),
    (r'(?<!\w)>(?!>)\s*/dev/',                        'HIGH',     '写入 /dev 设备文件'),

    # 权限 / 提权
    (r'\bsudo\s+rm\b',                               'CRITICAL', 'sudo rm 会以 root 权限删除文件'),
    (r'\bchmod\s+-R\s+777\b',                        'HIGH',     '递归 777 权限——严重安全隐患'),
    (r'\bchown\b',                                   'MEDIUM',   'chown 改变文件所有者'),

    # 文件泄露/覆盖
    (r'(?:>|>>)\s+/(?:etc|boot|dev|proc|sys)/',      'CRITICAL', '写入系统关键路径'),
    (r'\bmv\s+.*\s+/\s*$',                           'HIGH',     '移动文件到根目录——可能破坏系统'),
    (r'\bcp\s+.*\s+/\s*$',                           'HIGH',     '复制文件到根目录'),
    (r'\bdd\s+if=.*\s+of=/dev/',                     'CRITICAL', 'dd 写入 /dev 设备——可能损坏硬件'),

    # 加密勒索 / 批量改名
    (r'\bmv\s+.*\s+.*\.encrypted\b',                 'HIGH',     '批量重命名为 .encrypted——疑似勒索软件'),
    (r'\bgpg\s+.*--symmetric\b',                     'MEDIUM',   '对称加密——和勒索软件模式相似'),

    # 网络操作（curl/wget 拦截不是全部，只拦往黑暗处的）
    (r'\bcurl\s+.*\|\s*(bash|sh|python)\b',          'HIGH',     'curl | bash 会执行不可信的远程脚本'),
    (r'\bwget\s+.*\|\s*(bash|sh|python)\b',          'HIGH',     'wget | bash 会执行不可信的远程脚本'),
]


def log_blocked(command, reason, severity):
    """记录被拦截的命令到 blocked.log"""
    log_dir = Path.home() / '.claude' / 'hooks'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'blocked.log'

    entry = json.dumps({
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        'severity': severity,
        'reason': reason,
        'command': command,
        'project_path': str(Path.cwd()),
    }, ensure_ascii=False)

    with open(log_file, 'a') as f:
        f.write(entry + '\n')


def check_command(command: str):
    """
    检查命令是否危险。
    返回 None = 安全，返回 dict = 有风险。
    """
    # 先剥离注释和非执行上下文
    # （注释行的内容不应触发拦截）
    stripped = _strip_non_executable(command)
    if not stripped:
        return None

    for pattern, severity, reason in BLOCKED_PATTERNS:
        if re.search(pattern, stripped, re.IGNORECASE):
            return {
                'blocked': True,
                'severity': severity,
                'reason': reason,
                'matched_pattern': pattern,
            }
    return None


def main():
    # Claude Code hook 协议：从 stdin 读取 JSON，从 stdout 输出 JSON
    try:
        raw = sys.stdin.read()
        if not raw:
            # 无输入＝正常退出
            print(json.dumps({"status": "ok", "message": "no input received"}))
            return

        payload = json.loads(raw)
    except json.JSONDecodeError:
        print(json.dumps({"status": "ok", "message": "invalid JSON input, skipping"}))
        return

    # 提取要执行的命令
    # Claude Code hook payload 格式：
    # {"tool_use": {"name": "bash", "input": {"command": "..."}}}
    tool_name = payload.get('tool_use', {}).get('name', '')
    command = ''

    if tool_name == 'bash':
        command = payload.get('tool_use', {}).get('input', {}).get('command', '')
    elif tool_name == 'execute_command':
        command = payload.get('tool_use', {}).get('input', {}).get('command', '')
    else:
        # 非 bash 工具，放行
        print(json.dumps({"status": "ok", "message": f"not a command tool: {tool_name}"}))
        return

    if not command:
        print(json.dumps({"status": "ok", "message": "empty command, skipping"}))
        return

    # 检查命令
    result = check_command(command)
    if result is None:
        print(json.dumps({"status": "ok", "message": "command is safe"}))
        return

    # 拦截！
    severity = result['severity']
    reason = result['reason']

    # 记录到日志
    log_blocked(command, reason, severity)

    # 输出拦截信息给 Claude
    blocked_msg = (
        f"🚫 BLOCKED ({severity}): {reason}\n"
        f"   Command: {command}\n"
        f"\n"
        f"If you believe this command is safe for this project, "
        f"please explain why in your response.\n"
        f"Blocked entries are logged to ~/.claude/hooks/blocked.log"
    )

    print(json.dumps({
        "status": "error",
        "error": {
            "type": "blocked_command",
            "message": blocked_msg,
        },
        "result": blocked_msg,
    }))


def _strip_non_executable(cmd: str) -> str:
    """除去纯注释行、markdown 代码块标记、代码字符串等非可执行内容"""
    lines = cmd.split('\n')
    cleaned = []
    for line in lines:
        line_stripped = line.strip()
        # 跳过纯注释行
        if line_stripped.startswith('#') or line_stripped.startswith('//'):
            continue
        # 跳过 markdown fenced code 标记
        if line_stripped.startswith('```'):
            continue
        # 跳过编程语言代码行（不是 shell 命令）
        if re.match(r'^(?:const|let|var|function|import|export|def |class |setTimeout)', line_stripped):
            continue
        # 跳过对象方法调用（如 db.delete().from()、console.log()）
        if re.match(r'^\w+\.\w+', line_stripped):
            continue
        cleaned.append(line)
    return '\n'.join(cleaned)


if __name__ == '__main__':
    main()
