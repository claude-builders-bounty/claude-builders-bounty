#!/usr/bin/env python3
"""changelog.py — 从 git 历史生成结构化 CHANGELOG.md

用法:
  python3 changelog.py                     # 最近 tag..HEAD
  python3 changelog.py -o CHANGELOG.md     # 指定输出
  python3 changelog.py -r v1.2.0..HEAD     # 指定范围
  python3 changelog.py --dry-run           # 只打印，不写文件
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

CATEGORIES = ("Added", "Changed", "Fixed", "Removed")

# conventional-commit 前缀 → 分类
PREFIX_RULES = (
    (("feat", "feature", "add"), "Added"),
    (("fix", "bugfix", "hotfix"), "Fixed"),
    (("refactor", "perf", "chore", "build", "ci", "style", "change", "update"), "Changed"),
    (("remove", "delete", "drop", "deprecate", "revert"), "Removed"),
)

# 中文/无前缀时的关键词兜底
KEYWORD_RULES = (
    (("新增", "增加", "添加", "支持"), "Added"),
    (("修复", "修正", "解决", "bug"), "Fixed"),
    (("删除", "移除", "废弃", "回滚"), "Removed"),
)


def run_git(args: list[str]) -> str:
    try:
        out = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError:
        sys.exit("找不到 git，请先安装 git 并加入 PATH")
    if out.returncode != 0:
        return ""
    return out.stdout.strip()


def classify(subject: str) -> str:
    s = subject.strip()
    lower = s.lower()

    # 1) conventional commit：取冒号前的部分
    head = re.split(r"[:：]", s, maxsplit=1)[0].strip().lower()
    head = re.sub(r"\(.*?\)", "", head)  # feat(api) -> feat
    for prefixes, cat in PREFIX_RULES:
        if head.startswith(prefixes):
            return cat

    # 2) 关键词兜底
    for words, cat in KEYWORD_RULES:
        if any(w in lower for w in words):
            return cat

    return "Changed"


def collect(rev_range: str) -> dict[str, list[str]]:
    raw = run_git(["log", "--no-merges", "--pretty=format:%h%x1f%s", rev_range])
    buckets: dict[str, list[str]] = {c: [] for c in CATEGORIES}
    if not raw:
        return buckets

    for line in raw.splitlines():
        if "\x1f" not in line:
            continue
        sha, subject = line.split("\x1f", 1)
        subject = subject.strip()
        if not subject:
            continue
        # 跳过合并提交和版本号提交
        if subject.lower().startswith("merge "):
            continue
        if re.fullmatch(r"[vV]?\d+\.\d+.*", subject):
            continue
        buckets[classify(subject)].append(f"- {subject} (`{sha[:7]}`)")
    return buckets


def render(buckets: dict[str, list[str]], version: str, from_tag: str, today: str) -> str:
    lines = [
        "# Changelog",
        "",
        "本项目的重要变更都记在这里，格式遵循 "
        "[Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。",
        "",
        f"## [{version}] - {today}",
        "",
    ]
    scope = f"`{from_tag}..HEAD`" if from_tag else "全部历史（没有找到 tag）"
    lines += [f"> 范围：{scope}", ""]

    total = sum(len(v) for v in buckets.values())
    for cat in CATEGORIES:
        items = buckets[cat]
        if not items:
            continue
        lines += [f"### {cat}", "", *items, ""]

    if total == 0:
        lines += ["_本次范围内没有可写入的提交。_", ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="从 git 历史生成结构化 CHANGELOG.md")
    ap.add_argument("-o", "--output", default="CHANGELOG.md", help="输出文件（默认 CHANGELOG.md）")
    ap.add_argument("-r", "--range", default="", help="提交范围，如 v1.0.0..HEAD")
    ap.add_argument("--dry-run", action="store_true", help="只打印，不写文件")
    args = ap.parse_args()

    if run_git(["rev-parse", "--git-dir"]) == "":
        sys.exit("这里不是 git 仓库")

    rev_range = args.range
    from_tag = ""
    if not rev_range:
        from_tag = run_git(["describe", "--tags", "--abbrev=0"])
        rev_range = f"{from_tag}..HEAD" if from_tag else "HEAD"

    version = run_git(["describe", "--tags", "--exact-match"]) or "Unreleased"
    text = render(collect(rev_range), version, from_tag, date.today().isoformat())

    if args.dry_run:
        print(text)
        return

    Path(args.output).write_text(text, encoding="utf-8")
    total = text.count("\n- ")
    print(f"已写入 {args.output}（{total} 条提交，范围 {rev_range}）")


if __name__ == "__main__":
    main()
