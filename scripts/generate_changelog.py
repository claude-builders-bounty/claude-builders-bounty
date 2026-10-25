#!/usr/bin/env python3
"""Generate a managed Unreleased block from reachable Git history."""

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

BEGIN = "<!-- git-changelog:begin -->"
END = "<!-- git-changelog:end -->"
CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


def git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True,
        encoding="utf-8", errors="replace", check=False,
    )
    if result.returncode:
        raise ValueError(result.stderr.strip() or "Git command failed")
    return result.stdout.strip()


def category(subject):
    conventional = re.match(r"^(\w+)(?:\([^)]*\))?!?:\s*(.*)$", subject)
    kind, text = (conventional.groups() if conventional else ("", subject))
    kind, text = kind.lower(), text.lower()
    # An explicit removal remains Removed even when written as feat!: remove ...
    if kind in {"remove", "removed", "delete", "drop"} or re.match(
        r"^(remove[sd]?|delet(?:e[sd]?|ing)|drop(?:ped|ping)?|removing)\b", text
    ):
        return "Removed"
    if kind in {"fix", "bugfix", "hotfix", "patch"} or re.match(
        r"^(fix(?:ed|es|ing)?|resolve[sd]?|repair(?:ed|s)?)\b", text
    ):
        return "Fixed"
    if kind in {"feat", "feature", "add"} or re.match(
        r"^(add(?:ed|s|ing)?|introduce[sd]?|implement(?:ed|s)?)\b", text
    ):
        return "Added"
    return "Changed"


def markdown(text):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"([\\`*_\[\]{}])", r"\\\1", text)


def history(repo):
    root = Path(git(repo, "rev-parse", "--show-toplevel"))
    if git(root, "rev-parse", "--is-shallow-repository") == "true":
        raise ValueError("Shallow history: run git fetch --unshallow --tags before generating.")
    head = git(root, "rev-parse", "--verify", "HEAD^{commit}")
    tagged = subprocess.run(
        ["git", "-C", str(root), "describe", "--tags", "--abbrev=0", head],
        capture_output=True, encoding="utf-8", errors="replace", check=False,
    )
    tag = tagged.stdout.strip() if tagged.returncode == 0 else None
    # Resolve to a commit ID before using a tag in a revision range.
    start = git(root, "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}") if tag else None
    revision = f"{start}..{head}" if start else head
    fields = git(root, "log", "--reverse", "--topo-order", "-z", "--format=%H%x00%s", revision, "--").split("\0")
    if fields[-1] == "":
        fields.pop()
    commits = list(zip(fields[::2], fields[1::2]))
    return root, tag, head, commits


def render(tag, commits):
    buckets = {name: [] for name in CATEGORIES}
    for sha, subject in commits:
        buckets[category(subject)].append(f"- {markdown(subject)} (`{sha[:12]}`)")
    boundary = f"since tag {markdown(tag)}" if tag else "from the beginning of history (no reachable tag)"
    lines = [BEGIN, f"Changes {boundary}.", ""]
    for name, entries in buckets.items():
        lines.extend([f"### {name}", "", *(entries or ["_No changes._"]), ""])
    return "\n".join([*lines, END])


def update_document(existing, block):
    starts, ends = existing.count(BEGIN), existing.count(END)
    if starts or ends:
        if starts != 1 or ends != 1 or existing.index(BEGIN) > existing.index(END):
            raise ValueError("Malformed or duplicate git-changelog markers; leaving the file unchanged.")
        return existing[:existing.index(BEGIN)] + block + existing[existing.index(END) + len(END):]
    unreleased = list(re.finditer(r"^##[ \t]+\[?Unreleased\]?(?:[ \t]+[^\n]*)?[ \t]*$", existing, re.M | re.I))
    if len(unreleased) > 1:
        raise ValueError("Multiple Unreleased sections; leaving the file unchanged.")
    if unreleased:
        pos = unreleased[0].end()
        return existing[:pos] + "\n\n" + block + "\n" + existing[pos:]
    section = "## [Unreleased]\n\n" + block + "\n\n"
    first_release = re.search(r"^##[ \t]+", existing, re.M)
    if first_release:
        return existing[:first_release.start()] + section + existing[first_release.start():]
    prefix = existing.rstrip() if existing.strip() else "# Changelog"
    return prefix + "\n\n" + section.rstrip() + "\n"


def atomic_write(path, content):
    if path.is_symlink():
        raise ValueError("Output is a symlink; choose a regular Markdown file.")
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Git working tree (default: current directory)")
    parser.add_argument("--output", type=Path, help="Output path relative to repository root (default: CHANGELOG.md)")
    parser.add_argument("--stdout", action="store_true", help="Print a standalone changelog without writing files")
    args = parser.parse_args()
    try:
        root, tag, head, commits = history(args.repo)
        block = render(tag, commits)
        if args.stdout:
            print(update_document("", block), end="")
            return 0
        target = args.output or Path("CHANGELOG.md")
        if not target.is_absolute():
            target = root / target
        if target.is_symlink():
            raise ValueError("Output is a symlink; choose a regular Markdown file.")
        existing = target.read_text(encoding="utf-8") if target.exists() else ""
        content = update_document(existing, block)
        if content != existing:
            atomic_write(target, content)
        print(f"{target}: {len(commits)} commits; {tag or 'no reachable tag'}..{head[:12]}")
        return 0
    except (OSError, ValueError, UnicodeError) as error:
        print(f"changelog: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
