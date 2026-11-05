#!/usr/bin/env python3
"""
CHANGELOG 生成器 · 千寻 D20261105-10（对应 $50 SKILL: structured CHANGELOG 悬赏）
-------------------------------------------------------------------------------
零依赖。把 git log 或纯文本提交记录按 Conventional Commits 分类，
输出 Keep a Changelog 格式。中文提交也能识别。

用法：
  python3 changelog_gen.py --repo . --version v1.0.0 -o CHANGELOG.md
  python3 changelog_gen.py --repo . --range v1.0.0..HEAD   # 只取某 tag 之后的提交
  bash changelog.sh [repo路径] [输出.md]                    # 自动从最后一个 tag 起算
  git log --pretty=format:'%h %s' | python3 changelog_gen.py --stdin
  echo -e 'feat: 新增导出\nfix: 修复空指针' | python3 changelog_gen.py --stdin
"""
import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

GROUPS = [
    ("Added", ["feat", "feature", "add", "新增", "添加", "新功能", "支持"]),
    ("Fixed", ["fix", "bug", "hotfix", "修复", "修正", "解决", "兼容"]),
    ("Changed", ["refactor", "perf", "style", "improve", "update", "重构", "优化", "改进", "升级"]),
    ("Deprecated", ["deprecate", "废弃", "弃用"]),
    ("Removed", ["remove", "delete", "删除", "移除"]),
    ("Security", ["security", "安全", "漏洞", "越权"]),
    ("Documentation", ["docs", "doc", "文档", "注释", "readme"]),
    ("Tests", ["test", "测试", "单测"]),
    ("Chore", ["chore", "build", "ci", "deps", "构建", "依赖", "配置"]),
]

CONV = re.compile(r"^\s*(?:\[?([a-f0-9]{6,12})\]?\s*)?(?:([a-z]+)(?:\([^)]*\))?!?\s*[:：]\s*)?(.+)$", re.I)


def classify(msg):
    low = msg.lower()
    for group, kws in GROUPS:
        if any(k in low for k in kws):
            return group
    return "Other"


def parse(line):
    m = CONV.match(line.strip())
    if not m:
        return None
    sha, kind, msg = m.group(1), (m.group(2) or "").lower(), m.group(3).strip()
    if not msg:
        return None
    group = next((g for g, kws in GROUPS if kind and any(k == kind or k.startswith(kind) for k in kws)), None)
    return {"sha": sha, "group": group or classify(msg), "msg": msg}


def render(entries, version, repo_note):
    grouped = {}
    for e in entries:
        grouped.setdefault(e["group"], []).append(e)
    L = ["# Changelog", "",
         "本项目所有值得注意的变更记录在此。格式遵循 Keep a Changelog，",
         "分类依据 Conventional Commits 与中文关键词识别。", "",
         f"## [{version}] - {date.today().isoformat()}", ""]
    for group, _ in GROUPS + [("Other", [])]:
        if group not in grouped:
            continue
        L.append(f"### {group}")
        for e in grouped[group]:
            sha = f"`{e['sha'][:7]}` " if e["sha"] else ""
            L.append(f"- {sha}{e['msg']}")
        L.append("")
    if repo_note:
        L += ["---", repo_note]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="零依赖 CHANGELOG 生成器")
    ap.add_argument("--repo", help="git 仓库路径（自动读取 git log）")
    ap.add_argument("--range", dest="rng", help="git log 范围，如 v1.0.0..HEAD（配合 --repo）")
    ap.add_argument("--stdin", action="store_true", help="从标准输入读提交记录")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--version", default="Unreleased")
    ap.add_argument("-o", "--output")
    args = ap.parse_args()

    if args.repo:
        rng = args.rng or "HEAD"
        try:
            raw = subprocess.check_output(
                ["git", "-C", args.repo, "log", rng, f"-{args.limit}",
                 "--pretty=format:%h %s", "--no-merges"],
                stderr=subprocess.DEVNULL, timeout=20).decode("utf-8", "replace")
            note = f"来源：git log {rng}（最近 {args.limit} 条，--no-merges）"
        except Exception as e:
            print(f"读取 git log 失败：{e}", file=sys.stderr)
            sys.exit(1)
    elif args.stdin or not sys.stdin.isatty():
        raw = sys.stdin.read()
        note = "来源：标准输入"
    else:
        print("请指定 --repo 或用管道传入提交记录（--stdin）", file=sys.stderr)
        sys.exit(1)

    entries = [x for x in (parse(l) for l in raw.splitlines()) if x]
    if not entries:
        print("未解析到有效提交记录", file=sys.stderr)
        sys.exit(1)
    md = render(entries, args.version, note)
    if args.output:
        Path(args.output).write_text(md, encoding="utf-8")
        print(f"已写入 {args.output}")
    else:
        print(md)
    print(f"[stats] 提交 {len(entries)} 条 / 分组 {len({e['group'] for e in entries})} 类", file=sys.stderr)


if __name__ == "__main__":
    main()
