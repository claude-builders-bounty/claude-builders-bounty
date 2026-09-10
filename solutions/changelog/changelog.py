"""Generate a changelog without executing text from commit messages."""
import argparse
from pathlib import Path
import re
import subprocess


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def category(subject):
    match = re.match(r"^(\w+)(?:\([^)]*\))?!?:\s*(.*)$", subject)
    kind, text = (match[1].lower(), match[2]) if match else ("", subject)
    if kind in ("remove", "removed") or re.match(r"^(remove|delete|drop)\b", text, re.I):
        return "Removed"
    if kind in ("feat", "add", "added") or re.match(r"^(add|introduce)\b", text, re.I):
        return "Added"
    if kind in ("fix", "fixed", "bugfix") or re.match(r"^(fix|repair)\b", text, re.I):
        return "Fixed"
    return "Changed"


def escape(text):
    return re.sub(r"([\\`*_{}\[\]<>])", r"\\\1", text)


def render(repo):
    if git(repo, "rev-parse", "--is-shallow-repository").strip() == b"true":
        raise ValueError("Shallow history: fetch full history and tags before generating.")
    head = git(repo, "rev-parse", "--verify", "HEAD").decode().strip()
    # Nearest tagged release on the current branch's first-parent history.
    try:
        tag = git(repo, "describe", "--tags", "--abbrev=0", "--first-parent", head).decode().strip()
    except subprocess.CalledProcessError:
        tag = None
    base = git(repo, "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}").decode().strip() if tag else None
    rev = f"{base}..{head}" if base else head
    raw = git(repo, "log", "--reverse", "--format=%H%x00%s", "-z", rev)
    fields = raw.decode("utf-8", errors="replace").split("\0")
    groups = {name: [] for name in ("Added", "Fixed", "Changed", "Removed")}
    for i in range(0, len(fields) - 1, 2):
        sha, subject = fields[i:i + 2]
        groups[category(subject)].append(f"- {escape(subject)} (`{sha[:12]}`)")
    lines = ["# Changelog", "", "## [Unreleased]", "",
             f"Source HEAD: `{head}`", "",
             f"Changes since {escape(tag)}." if tag else "No reachable release tag; includes all commits.", ""]
    for name, entries in groups.items():
        lines.extend([f"### {name}", "", *(entries or ["- None."]), ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("CHANGELOG.md"))
    args = parser.parse_args()
    try:
        content = render(args.repo)
        # Exclusive creation protects an existing hand-maintained changelog.
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(content)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"changelog: {exc}\n")


if __name__ == "__main__":
    main()
