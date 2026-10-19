#!/usr/bin/env python3
"""Generate a Keep a Changelog-style draft from commits since the last tag."""

from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path


SECTIONS = ("Added", "Fixed", "Changed", "Removed")
CONVENTIONAL = re.compile(r"^(?P<type>[a-zA-Z]+)(?:\([^)]*\))?(?P<breaking>!)?:\s*(?P<subject>.+)$")


def git(*args: str, cwd: Path) -> str:
    """Run git without a shell and return UTF-8 output."""
    result = subprocess.run(
        ["git", *args], cwd=cwd, check=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
    )
    return result.stdout


def last_reachable_tag(cwd: Path) -> str | None:
    reachable_tags = git("tag", "--merged", "HEAD", "--list", cwd=cwd).strip()
    if not reachable_tags:
        return None
    tag = git("describe", "--tags", "--abbrev=0", "HEAD", cwd=cwd).strip()
    return tag or None


def commits_since_tag(cwd: Path, tag: str | None) -> list[tuple[str, str]]:
    # A tag name can also resolve to a pseudoref or a fully qualified branch.
    # Keep the release boundary in the tag namespace and separate path arguments.
    revision = f"refs/tags/{tag}..HEAD" if tag else "HEAD"
    raw = git("log", "--no-show-signature", "--encoding=UTF-8", "--format=%H%x00%s%x00", revision, "--", cwd=cwd)
    parts = raw.split("\0")
    commits = []
    for index in range(0, len(parts) - 1, 2):
        commit_hash, subject = parts[index:index + 2]
        if commit_hash:
            commits.append((commit_hash, subject.strip()))
    return commits


def classify(subject: str) -> tuple[str, str]:
    """Return (section, readable subject), defaulting untyped commits to Changed."""
    match = CONVENTIONAL.match(subject.strip())
    if not match:
        return "Changed", escape_markdown(subject.strip())
    kind = match.group("type").lower()
    section = {
        "feat": "Added", "add": "Added",
        "fix": "Fixed", "bug": "Fixed",
        "remove": "Removed", "deprecate": "Removed",
    }.get(kind, "Changed")
    description = match.group("subject").strip()
    if match.group("breaking"):
        description = f"**BREAKING:** {escape_markdown(description)}"
        return section, description
    return section, escape_markdown(description)


def escape_markdown(text: str) -> str:
    """Render an untrusted commit subject as plain text in a Markdown list."""
    escaped = html.escape(text, quote=False)
    for char in ("\\", "`", "*", "_", "{", "}", "[", "]", "(", ")", "#", "+", "-", ".", "!", "|", "~", ">", ":", "@"):
        escaped = escaped.replace(char, "\\" + char)
    return escaped


def render(commits: list[tuple[str, str]], tag: str | None) -> str:
    groups: OrderedDict[str, list[str]] = OrderedDict((name, []) for name in SECTIONS)
    for _commit_hash, subject in commits:
        section, description = classify(subject)
        groups[section].append(description)

    title = f"## Unreleased (since {escape_markdown(tag)})" if tag else "## Unreleased"
    lines = ["# Changelog", "", title, ""]
    if not commits:
        lines.extend(["No changes since the last tag.", ""])
        return "\n".join(lines)
    for section, entries in groups.items():
        if entries:
            lines.extend([f"### {section}", ""])
            lines.extend(f"- {entry}" for entry in entries)
            lines.append("")
    return "\n".join(lines)


def generate(cwd: Path) -> str:
    tag = last_reachable_tag(cwd)
    commits = commits_since_tag(cwd, tag)
    return render(commits, tag)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Git repository (default: current directory)")
    parser.add_argument("--output", type=Path, default=Path("CHANGELOG.md"), help="output file (default: CHANGELOG.md)")
    parser.add_argument("--force", action="store_true", help="replace the output file if it already exists")
    args = parser.parse_args(argv)
    try:
        repo = args.repo.resolve()
        content = generate(repo)
        output = args.output if args.output.is_absolute() else repo / args.output
        if args.force:
            output.write_text(content, encoding="utf-8")
        else:
            # Exclusive creation prevents silent truncation, including if the
            # file appears between checking and opening it.
            with output.open("x", encoding="utf-8") as changelog:
                changelog.write(content)
    except (OSError, subprocess.CalledProcessError) as error:
        detail = error.stderr.strip() if isinstance(error, subprocess.CalledProcessError) and error.stderr else str(error)
        print(f"changelog: {detail}", file=sys.stderr)
        return 1
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
