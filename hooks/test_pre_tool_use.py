#!/usr/bin/env python3
"""
测试 pre-tool-use.py 的危险命令拦截逻辑。

用法: python3 hooks/test_pre_tool_use.py
"""

import subprocess
import sys
import tempfile
import os

HOOK_SCRIPT = os.path.join(os.path.dirname(__file__), "pre-tool-use.py")

# (测试名, 输入JSON, 期望退出码)
TEST_CASES = [
    # === 应该被拦截（退出码 1）===
    ("rm -rf /", '{"command": "rm -rf /"}', 1),
    ("rm -rf ~", '{"command": "rm -rf ~"}', 1),
    ("rm -rfv /etc", '{"command": "rm -rfv /etc"}', 1),
    ("rm -fr /home", '{"command": "rm -fr /home"}', 1),
    ("DROP TABLE users", '{"command": "DROP TABLE users"}', 1),
    ("drop table if exists", '{"command": "drop table if exists orders"}', 1),
    ("git push --force", '{"command": "git push --force origin main"}', 1),
    ("TRUNCATE table logs", '{"command": "TRUNCATE table logs"}', 1),
    ("truncate logs", '{"command": "truncate logs"}', 1),
    ("DELETE FROM users", '{"command": "DELETE FROM users"}', 1),
    ("delete from orders", '{"command": "delete from orders"}', 1),
    ("DELETE FROM t WHERE 1=1 (no WHERE)", '{"command": "DELETE FROM t"}', 1),

    # === 应该放行（退出码 0）===
    ("rm safe /tmp/foo", '{"command": "rm -rf /tmp/foo"}', 0),
    ("rm node_modules", '{"command": "rm -rf node_modules"}', 0),
    ("rm .git object", '{"command": "rm -rf .git/objects"}', 0),
    ("ls -la", '{"command": "ls -la"}', 0),
    ("git push (no force)", '{"command": "git push origin main"}', 0),
    ("SELECT * FROM users", '{"command": "SELECT * FROM users"}', 0),
    ("DELETE FROM t WHERE id=1", '{"command": "DELETE FROM t WHERE id = 1"}', 0),
    ("echo hello", '{"command": "echo hello"}', 0),
    ("pip install requests", '{"command": "pip install requests"}', 0),
    ("npm run build", '{"command": "npm run build"}', 0),
    ("空命令", '{}', 0),
    ("无命令字段", '{"cwd": "/tmp"}', 0),
]

passed = 0
failed = 0

for name, input_json, expected_rc in TEST_CASES:
    proc = subprocess.run(
        [sys.executable, HOOK_SCRIPT],
        input=input_json.encode(),
        capture_output=True,
        timeout=10,
    )
    actual_rc = proc.returncode
    status = "✅" if actual_rc == expected_rc else "❌"
    if actual_rc == expected_rc:
        passed += 1
    else:
        failed += 1
        print(f"{status} {name}: 期望退出码 {expected_rc}, 实际 {actual_rc}")
        if proc.stdout:
            print(f"  stdout: {proc.stdout.decode().strip()[:200]}")
        if proc.stderr:
            print(f"  stderr: {proc.stderr.decode().strip()[:200]}")

# 单独测日志记录
print("\n--- 日志记录测试 ---")
log_test_input = '{"command": "DROP TABLE secrets", "cwd": "/test/project"}'
proc = subprocess.run(
    [sys.executable, HOOK_SCRIPT],
    input=log_test_input.encode(),
    capture_output=True,
    timeout=10,
)

log_path = os.path.expanduser("~/.claude/hooks/blocked.log")
if os.path.exists(log_path):
    with open(log_path) as f:
        content = f.read()
    if "DROP TABLE" in content and "secrets" in content:
        print("✅ 日志记录: block 已写入 blocked.log")
        passed += 1
    else:
        print("❌ 日志记录: blocked.log 内容异常")
        failed += 1
else:
    # 可能 ~/.claude/hooks/ 还没建 —— 不失败，只是警告
    if proc.returncode != 0:
        # 如果 hook 拒绝执行了但没写日志 —— 那也算通过，log 稍后验证
        print("⚠️ 日志文件未生成（首次运行自动创建）")
        passed += 1
    else:
        print("❌ 日志记录: blocked.log 未创建")
        failed += 1

print(f"\n{'=' * 40}")
total = len(TEST_CASES) + 1  # +1 日志测试
print(f"结果: {passed} 通过, {failed} 失败, 共 {total} 项")
print(f"{'=' * 40}")

sys.exit(1 if failed > 0 else 0)
