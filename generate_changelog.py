#!/usr/bin/env python3
"""Generate a deterministic changelog draft from local Git commit subjects."""
import argparse
import html
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")
PREFIXES = {
    "feat": "Added", "feature": "Added", "add": "Added",
    "fix": "Fixed", "bugfix": "Fixed", "hotfix": "Fixed",
    "remove": "Removed", "delete": "Removed", "drop": "Removed",
}
CONVENTIONAL = re.compile(r"^([a-z]+)(?:\([^)]*\))?!?:\s*(.+)$", re.I)
VERBS = re.compile(r"^(add(?:ed)?|introduce[ds]?|implement(?:ed)?|fix(?:ed)?|resolve[ds]?|remove[ds]?|delete[ds]?|drop(?:ped)?)\b", re.I)


class ChangelogError(Exception):
    pass


def git(repo, *args, allow_failure=False, raw=False):
    decoding = {} if raw else {"text": True, "encoding": "utf-8", "errors": "replace"}
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True,
        **decoding,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if result.returncode and not allow_failure:
        error = result.stderr.decode("utf-8", errors="replace") if raw else result.stderr
        raise ChangelogError(error.strip() or "Git command failed")
    return result


def categorize(subject):
    match = CONVENTIONAL.match(subject)
    if match:
        return PREFIXES.get(match[1].lower(), "Changed"), match[2]
    match = VERBS.match(subject)
    if match:
        word = match[1].lower()
        if word.startswith(("add", "introduc", "implement")):
            return "Added", subject
        if word.startswith(("fix", "resolv")):
            return "Fixed", subject
        return "Removed", subject
    return "Changed", subject


def markdown(text):
    # Subjects are untrusted text, not executable shell or Markdown markup.
    text = html.escape(text, quote=False)
    text = "".join(char if ord(char) >= 32 and ord(char) != 127 else " " for char in text)
    return re.sub(r"([\\`*_\[\]])", r"\\\1", text)


def generate(repo):
    # Remove only Git's terminator, preserving whitespace and raw path bytes.
    top = git(repo, "rev-parse", "--show-toplevel", raw=True).stdout
    root = Path(os.fsdecode(top[:-1] if top.endswith(b"\n") else top))
    if git(root, "rev-parse", "--verify", "HEAD", allow_failure=True).returncode:
        raise ChangelogError("repository has no commits")
    tag_result = git(root, "describe", "--tags", "--abbrev=0", "HEAD", allow_failure=True)
    tag = tag_result.stdout.strip() if tag_result.returncode == 0 else None
    revision = f"refs/tags/{tag}..HEAD" if tag else "HEAD"
    log = git(root, "log", "--reverse", "--topo-order", "--format=%H%x00%s%x00", revision, "--").stdout
    groups = {name: [] for name in CATEGORIES}
    fields = log.split("\0")
    for index in range(0, len(fields) - 1, 2):
        commit, subject = fields[index].strip("\n"), fields[index + 1]
        category, title = categorize(subject)
        groups[category].append(f"- {markdown(title)} (`{commit[:12]}`)")
    scope = f"Changes since `{markdown(tag)}`." if tag else "Changes from all available history (no reachable tag)."
    lines = ["# Changelog", "", "## [Unreleased]", "", scope, ""]
    for category in CATEGORIES:
        lines.extend([f"### {category}", "", *(groups[category] or ["_No changes._"]), ""])
    return root, "\n".join(lines)


def write_output(path, content, overwrite):
    if not overwrite:
        # O_EXCL also refuses dangling symlinks and prevents a check/write race.
        try:
            with path.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
        except FileExistsError:
            raise ChangelogError(f"{path} already exists; review it or pass --overwrite") from None
    else:
        # Replace the directory entry, never follow an output symlink.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(content)
            temporary.replace(path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="repository directory (default: current directory)")
    parser.add_argument("--output", type=Path, help="output file (default: repository root/CHANGELOG.md; relative paths use current directory)")
    parser.add_argument("--overwrite", action="store_true", help="explicitly replace an existing output file")
    args = parser.parse_args()
    try:
        root, content = generate(args.repo)
        output = args.output if args.output is not None else root / "CHANGELOG.md"
        write_output(output, content, args.overwrite)
        print(f"Wrote {output}")
    except (ChangelogError, OSError, ValueError) as error:
        print(f"changelog: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
