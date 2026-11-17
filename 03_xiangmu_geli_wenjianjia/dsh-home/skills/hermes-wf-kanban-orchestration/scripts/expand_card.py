#!/usr/bin/env python
"""Expand an EXISTING kanban card: append (never overwrite), optionally retitle, verify.

Why a script instead of three hand edits: the same edit has failed three different ways
  · a heredoc/shell-concatenated body mangled CJK + full-width punctuation, no card touched
  · an overwriting edit silently dropped the card's original acceptance criteria
  · a natural new title collided with WF_VERIFY_KEYWORDS, which exempted the card from
    the produce-check so a worker could close it with an empty report

Usage
-----
  python expand_card.py --board xianyu --card t_xxxx --append-file add.md \
      --marker "【本卡职责升级"

  # also retitle (re-checked against WF_VERIFY_KEYWORDS)
  python expand_card.py --board xianyu --card t_xxxx --append-file add.md \
      --marker "【本卡职责升级" \
      --title "[R7-B5] 框架维护：修 A + 修复 B + 实现 C"

Idempotent: if --marker is already in the body, the append is skipped (the title is still
re-applied). Exit code is non-zero if any assertion fails.

Assertions on read-back
  · marker present in the body
  · the ORIGINAL body is still an exact prefix of the new body (nothing was dropped)
  · with --title: title matches AND contains no WF_VERIFY_KEYWORDS entry
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

# Mirrors WF_VERIFY_KEYWORDS in the workflow's config.env (config.env wins when it exists).
DEFAULT_KEYWORDS = ["验收", "巡检", "复核", "盘点", "闭环", "演练", "审计", "只读", "排查", "对照实验"]

MAX_CLI_BODY = 30000  # Windows command line caps near 32k; stay clear of it


def find_hermes(explicit):
    """Resolve the hermes executable. MUST be a native path: MSYS /d/... forms make
    subprocess raise FileNotFoundError [WinError 2] before the CLI ever runs."""
    for cand in (explicit, os.environ.get("HERMES_BIN"), os.environ.get("WF_HERMES_BIN")):
        if cand and os.path.isfile(cand):
            return cand
    found = shutil.which("hermes") or shutil.which("hermes.exe")
    if found:
        return found
    sys.exit(
        "找不到 hermes 可执行文件。传 --hermes 或设 HERMES_BIN。\n"
        "必须是原生路径（D:/.../venv/Scripts/hermes.exe）—— MSYS 的 /d/... 会让 subprocess 报 WinError 2。"
    )


def load_keywords(config_env):
    """Read the live WF_VERIFY_KEYWORDS so the check matches what the dispatcher enforces."""
    if config_env and os.path.isfile(config_env):
        import re
        text = open(config_env, encoding="utf-8", errors="replace").read()
        m = re.search(r'WF_VERIFY_KEYWORDS="([^"]*)"', text)
        if m:
            kws = [k.strip() for k in m.group(1).split(",") if k.strip()]
            if kws:
                return kws, f"config.env ({len(kws)} 项)"
    return DEFAULT_KEYWORDS, "内置默认表"


def run(hermes, board, *args):
    return subprocess.run(
        [hermes, "kanban", "--board", board, *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def show(hermes, board, card):
    r = run(hermes, board, "show", card, "--json")
    if r.returncode != 0:
        sys.exit(f"show {card} 失败: {(r.stdout + r.stderr).strip()[:300]}")
    payload = json.loads(r.stdout)
    return payload.get("task") or payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--card", required=True)
    ap.add_argument("--append-file", required=True, help="UTF-8 markdown to APPEND (never replaces)")
    ap.add_argument("--marker", required=True, help="idempotency token; presence means already applied")
    ap.add_argument("--title", default=None, help="new title; re-checked against WF_VERIFY_KEYWORDS")
    ap.add_argument("--hermes", default=None)
    ap.add_argument("--config-env", default=None, help="path to the workflow config.env (for WF_VERIFY_KEYWORDS)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    hermes = find_hermes(args.hermes)
    keywords, kw_src = load_keywords(args.config_env)
    addition = open(args.append_file, encoding="utf-8").read()
    if not addition.strip():
        sys.exit("--append-file 是空的 —— 拒绝用空内容改卡")

    task = show(hermes, args.board, args.card)
    old_body = task.get("body") or ""
    old_title = task.get("title") or ""

    if args.marker in old_body:
        new_body = old_body
        print(f"  正文已含 marker「{args.marker}」→ 跳过追加（幂等）")
    else:
        new_body = old_body + addition
        print(f"  正文追加: {len(old_body)} → {len(new_body)} 字符")

    if len(new_body) > MAX_CLI_BODY:
        sys.exit(f"正文 {len(new_body)} 字符超过命令行安全上限 {MAX_CLI_BODY} —— 拆成两张卡，"
                 f"或改为分次追加（每次一个 marker）")

    new_title = args.title or old_title
    if new_title != old_title:
        print(f"  标题: {old_title}")
        print(f"     → {new_title}")

    if args.dry_run:
        print("\n  [dry-run] 未写入")
        return 0

    edit_args = ["edit", args.card, "--body", new_body]
    if new_title != old_title:
        edit_args += ["--title", new_title]
    r = run(hermes, args.board, *edit_args)
    if r.returncode != 0:
        sys.exit(f"edit 失败: {(r.stdout + r.stderr).strip()[:300]}")

    after = show(hermes, args.board, args.card)
    body_after = after.get("body") or ""
    title_after = after.get("title") or ""

    checks = {
        "marker 已在正文": args.marker in body_after,
        "原正文完整保留（前缀一致）": body_after.startswith(old_body),
        "正文没有缩短": len(body_after) >= len(old_body),
        "标题已生效": title_after == new_title,
        f"标题未命中验收关键词（{kw_src}）": not [k for k in keywords if k in title_after],
    }
    print()
    for label, ok in checks.items():
        print(f"  {'✓' if ok else '✗'} {label}")
    hits = [k for k in keywords if k in title_after]
    if hits:
        print(f"\n  ⚠ 标题命中 {hits} —— card_produce_check 会把「零产出」判成合法，"
              f"worker 交空报告也能过。改用 修/修复/新增/实现 这类动作词，把巡检类措辞留在正文。")
    print(f"\n  正文最终长度: {len(body_after)} 字符")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
