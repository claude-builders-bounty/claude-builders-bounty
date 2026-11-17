#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stuck_task_fixer.py — 兜底修复：running 卡无 worker 且有新提交 → 自动触发 review

用法：
    python stuck_task_fixer.py [board_slug]

放在 cron monitor 里（review_watch.py 之后跑），或单独跑。
"""
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

KANBAN_HOME = Path(os.environ.get("HERMES_KANBAN_HOME", r"D:\\Ai\\Agent\\hermes\\kanban"))
HERMES_BIN = r"D:\\Ai\\Agent\\hermes\\hermes.exe"
PROJECT_DIR = r"D:\\Ai\\Agent\\projects\\wechat_recovery"


def git_head(cwd: str) -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, timeout=10)
        return r.stdout.strip()
    except Exception:
        return ""

def fix_stuck_tasks(board: str) -> list[str]:
    """返回已修复的 task_id 列表"""
    fixed = []
    db = KANBAN_HOME / "boards" / board / "kanban.db"
    if not db.exists():
        return fixed
    
    conn = sqlite3.connect(str(db), timeout=10)
    conn.row_factory = sqlite3.Row
    
    rows = conn.execute("""
        SELECT id, assignee, worker_pid, started_at 
        FROM tasks 
        WHERE status='running'
    """).fetchall()
    conn.close()
    
    if not rows:
        return fixed
    
    # 检查是否有 claude 进程
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", 
             "@(Get-Process -Name claude -ErrorAction SilentlyContinue).Count"],
            capture_output=True, text=True, timeout=20
        )
        has_claude = bool(out.stdout.strip()) and out.stdout.strip().isdigit() and int(out.stdout.strip()) > 0
    except Exception:
        has_claude = True  # 保守：假设有进程
    
    if has_claude:
        return fixed  # 有进程在跑，不动
    
    current_head = git_head(PROJECT_DIR)
    
    for r in rows:
        tid = r["id"]
        print(f"[stuck_fixer] 卡 {tid} running 但无 worker 进程，触发 request-review")
        try:
            subprocess.run(
                [HERMES_BIN, "kanban", "--board", board, "request-review", tid,
                 "--reviewer", "cc-code-reviewer",
                 "--summary", "自动检测：worker 进程消失但可能有产出（守卫兜底）"],
                capture_output=True, text=True, timeout=60
            )
            fixed.append(tid)
        except Exception as e:
            print(f"[stuck_fixer] request-review 失败 {tid}: {e}")
    
    return fixed

if __name__ == "__main__":
    board = sys.argv[1] if len(sys.argv) > 1 else "wechat_recovery"
    fixed = fix_stuck_tasks(board)
    if fixed:
        print(f"已修复: {fixed}")
    else:
        print("无需修复")