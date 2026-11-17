#!/usr/bin/env python
"""Acceptance audit for a hermes-wf kanban board. READ-ONLY.

Answers the two questions a coordinator must never answer from memory:

  1. Did any card actually pass through a review stage?
     -> counts review-ish kinds in task_events (0 = the lane never ran).
  2. Which `done` cards carry no evidence of accepted work?
     -> per card: does a commit mention the card id? did the worker admit that
        acceptance commands were never executed?

Usage:
  python acceptance_audit.py --board <slug> --repo D:/path/to/repo
  python acceptance_audit.py --board <slug> --repo ... --logs <dir>/logs/workers --db <kanban.db>

Exit code is always 0: this is a report, not a gate. Read the summary.
"""
import argparse
import os
import re
import sqlite3
import subprocess
import sys

# Kinds that would prove a review lane exists at all.
REVIEW_KINDS = ("review", "reviewed", "requested_review", "request_changes", "reopened_review")

# Phrases a worker uses when it admits acceptance never ran. Case-insensitive.
SELF_ADMIT = (
    "未执行", "未跑", "未运行", "补跑", "证据缺失", "无法执行", "无法产出命令",
    "no shell", "no bash", "无 shell", "无shell", "缺 shell", "缺shell",
    "无 bash", "无bash", "没有 bash", "没有bash", "无命令工具", "没有命令工具",
    "建议标记 review", "建议标记 `review`",
)


def find_db(board, explicit):
    if explicit:
        return explicit if os.path.exists(explicit) else None
    roots = [
        os.environ.get("HERMES_HOME"),
        os.path.expanduser("~/hermes"),
        os.path.expanduser("~/.hermes"),
        "D:/Ai/Agent/hermes",
    ]
    for r in roots:
        if not r:
            continue
        p = os.path.join(r, "kanban", "boards", board, "kanban.db")
        if os.path.exists(p):
            return p
    return None


def guess_logs(board):
    roots = [
        os.environ.get("HERMES_HOME"),
        os.path.expanduser("~/hermes"),
        "D:/Ai/Agent/hermes",
    ]
    for r in roots:
        if not r:
            continue
        for sub in (f"scripts/hermes-wf-{board}", "scripts/hermes-wf"):
            p = os.path.join(r, sub, "logs", "workers")
            if os.path.isdir(p):
                return p
    return None


def commit_count(repo, card_id):
    """How many commits in any branch mention the card id. None if git failed."""
    try:
        r = subprocess.run(
            ["git", "-C", repo, "log", "--all", "--oneline", f"--grep={card_id}"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
        )
    except Exception:
        return None
    if r.returncode != 0:
        return None
    return len([ln for ln in r.stdout.splitlines() if ln.strip()])


def log_self_admit(logs_dir, card_id):
    """Return the first self-admission phrase found in the worker log, or None."""
    if not logs_dir:
        return None
    p = os.path.join(logs_dir, f"{card_id}.out")
    if not os.path.exists(p):
        return None
    try:
        text = open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        return None
    low = text.lower()
    for phrase in SELF_ADMIT:
        if phrase.lower() in low:
            return phrase
    return None


def compact_chain(cur, task_id, limit=12):
    kinds = [r[0] for r in cur.execute(
        "SELECT kind FROM task_events WHERE task_id=? ORDER BY rowid", (task_id,))]
    out = kinds[:]
    dedup = [out[0]] if out else []
    for k in out[1:]:
        if k != dedup[-1]:
            dedup.append(k)
    if len(dedup) > limit:
        dedup = dedup[:limit] + ["…"]
    return " → ".join(dedup)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True, help="kanban board slug, e.g. xianyu")
    ap.add_argument("--repo", required=True, help="repo root the workers commit into")
    ap.add_argument("--logs", default=None, help="worker log dir (default: auto-detect)")
    ap.add_argument("--db", default=None, help="kanban.db path (default: auto-detect)")
    args = ap.parse_args()

    db = find_db(args.board, args.db)
    if not db:
        print(f"!! kanban.db not found for board '{args.board}'. Pass --db <path>.")
        return 0
    logs = args.logs or guess_logs(args.board)

    print(f"board    : {args.board}")
    print(f"db       : {db}")
    print(f"repo     : {args.repo}")
    print(f"logs     : {logs or '(not found — self-admission scan skipped)'}")
    print()

    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    cur = con.cursor()

    # --- 1. did a review lane ever run? -------------------------------------
    kinds = {r[0]: r[1] for r in cur.execute(
        "SELECT kind, COUNT(*) FROM task_events GROUP BY kind ORDER BY COUNT(*) DESC")}
    review_hits = {k: n for k, n in kinds.items() if any(t in k.lower() for t in REVIEW_KINDS)}
    print("== ① review 通道是否跑过 ==")
    print(f"   事件类型数: {len(kinds)}   总事件: {sum(kinds.values())}")
    print(f"   review 相关 kind: {review_hits or '无  <-- 从没跑过'}")
    statuses = {r[0]: r[1] for r in cur.execute(
        "SELECT status, COUNT(*) FROM tasks GROUP BY status")}
    print(f"   当前状态分布: {statuses}")
    if not review_hits:
        print("   => 结论：没有任何卡走过 review。若原设计里验收是协调者的人工动作，")
        print("      这不是链路 bug，是你这一侧没做（见 SKILL.md「验收是协调者自己的动作」）。")
    print()

    # --- 2. per done card: evidence of accepted work -------------------------
    done = list(cur.execute(
        "SELECT id, title FROM tasks WHERE status='done' ORDER BY completed_at"))
    print(f"== ② done 卡验收证据（共 {len(done)} 张）==")
    if done:
        print(f"   {'卡号':<14} {'有本卡 commit':<14} {'worker 自述未验收':<18} 状态链")
        print("   " + "-" * 96)

    no_commit, admitted, unknown = [], [], []
    for tid, title in done:
        n = commit_count(args.repo, tid)
        adm = log_self_admit(logs, tid)
        commit_cell = "?" if n is None else (f"{n} 个" if n else "0  <-- 无")
        adm_cell = adm or "-"
        if n == 0:
            no_commit.append(tid)
        if adm:
            admitted.append(tid)
        if n is None:
            unknown.append(tid)
        print(f"   {tid:<14} {commit_cell:<14} {adm_cell:<18} {compact_chain(cur, tid)[:40]}")
        print(f"   {'':14} {(title or '')[:70]}")

    print()
    print("== ③ 汇总 ==")
    print(f"   done 总数            : {len(done)}")
    print(f"   无本卡 commit        : {len(no_commit)} {no_commit if no_commit else ''}")
    print(f"   worker 自述未验收    : {len(admitted)} {admitted if admitted else ''}")
    print(f"   git 无法判定         : {len(unknown)}")
    print()
    print("   处置：无 commit 的卡按验收三步复查；自述未验收的卡要么补跑验收，")
    print("         要么如实标注为「仅交付未验收」—— 不要因为它们显示 done 就当验过。")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
