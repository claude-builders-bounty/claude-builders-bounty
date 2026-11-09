#!/usr/bin/env python3
"""Generate an unreleased changelog from local Git history (Python 3.9+)."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def git(repo, *args):
    """#1：参数列表避免 shell 求值；提交信息始终按数据处理。"""
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                            encoding="utf-8", errors="replace")
    if result.returncode:
        raise ValueError(result.stderr.strip() or "Git command failed")
    return result.stdout


def markdown(text):
    """转义提交标题中的 Markdown/HTML，避免意外链接或文档结构注入。"""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"([\\`*{}_\[\]()#!|])", r"\\\1", text)


def categorize(subject):
    """按 Conventional Commits 分类；无法识别的提交保留在 Changed。"""
    match = re.match(r"^([a-z]+)(?:\([^)]*\))?(!)?:\s*(.*)$", subject, re.I)
    if match:
        kind, breaking, title = match.groups()
    else:
        kind = subject.split(maxsplit=1)[0].lower() if subject else ""
        breaking, title = False, subject
    groups = {
        "feat": "Added", "add": "Added", "added": "Added",
        "fix": "Fixed", "fixed": "Fixed", "bugfix": "Fixed",
        "remove": "Removed", "removed": "Removed", "delete": "Removed",
    }
    return groups.get(kind.lower(), "Changed"), bool(breaking), title


def generate(repo, since):
    """仅使用可从 HEAD 到达的 tag；无 tag 时包含第一个提交。"""
    try:
        git(repo, "rev-parse", "--git-dir")
    except ValueError as exc:
        raise ValueError("Not a Git repository: " + str(repo)) from exc
    try:
        git(repo, "rev-parse", "--verify", "HEAD^{commit}")
    except ValueError as exc:
        raise ValueError("Repository has no commits") from exc
    if since is not None:
        try:
            base = git(repo, "rev-parse", "--verify", "--end-of-options", since + "^{commit}").strip()
        except ValueError as exc:
            raise ValueError("Invalid starting reference: " + since) from exc
        label = since
    else:
        try:
            label = git(repo, "describe", "--tags", "--abbrev=0", "HEAD").strip()
            base = git(repo, "rev-parse", "--verify", "refs/tags/" + label + "^{commit}").strip()
        except ValueError:
            label, base = None, None
    revision = base + "..HEAD" if base else "HEAD"
    # NUL 分隔三个字段，换行及自定义分隔字符不会破坏提交记录。
    fields = git(repo, "log", "-z", "--reverse", "--format=%H%x00%s%x00%b", revision, "--").split("\0")
    groups = {name: [] for name in ("Added", "Fixed", "Changed", "Removed")}
    for index in range(0, len(fields) - 1, 3):
        sha, subject, body = fields[index:index + 3]
        group, breaking, title = categorize(subject)
        breaking = breaking or bool(re.search(r"^BREAKING[ -]CHANGE:", body, re.M))
        marker = "**BREAKING** " if breaking else ""
        groups[group].append("- " + marker + markdown(title) + " (`" + sha[:7] + "`)")
    lines = ["# Changelog", "", "## [Unreleased]", "",
             "Changes since " + ("`" + markdown(label) + "`." if label else "the beginning of history."), ""]
    for group, entries in groups.items():
        if entries:
            lines.extend(["### " + group, "", *entries, ""])
    if not any(groups.values()):
        lines.extend(["No changes since the selected reference.", ""])
    return "\n".join(lines)


def write_output(target, content, force):
    """默认独占创建以保护历史；显式覆盖先写临时文件，防止写入中断截断旧文件。"""
    if not force:
        with target.open("x", encoding="utf-8") as stream:
            stream.write(content)
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent,
                                         prefix=".changelog-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(str(temporary), str(target))
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Local Git repository (default: cwd)")
    parser.add_argument("--since", help="Override the nearest reachable tag with a commit/tag/ref")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--output", type=Path, default=Path("CHANGELOG.md"), help="Output file relative to cwd")
    output.add_argument("--stdout", action="store_true", help="Print Markdown without writing a file")
    parser.add_argument("--force", action="store_true", help="Explicitly replace an existing output file")
    args = parser.parse_args()
    try:
        content = generate(args.repo, args.since)
        if args.stdout:
            sys.stdout.write(content)
        else:
            write_output(args.output, content, args.force)
            print("Wrote " + str(args.output))
    except (ValueError, OSError) as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
