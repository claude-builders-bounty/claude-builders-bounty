#!/usr/bin/env python3
"""Generate a deterministic changelog from local Git history. No dependencies."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

START = "<!-- generate-changelog:start -->"
END = "<!-- generate-changelog:end -->"
CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


class ChangelogError(Exception):
    pass


def git(repo: Path, *args: str, optional: bool = False) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True,
            encoding="utf-8", errors="replace", timeout=60, check=False,
        )
    except FileNotFoundError as exc:
        raise ChangelogError("Git is not installed or is not on PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise ChangelogError("Git command exceeded the 60-second limit.") from exc
    if result.returncode:
        if optional:
            return None
        raise ChangelogError("Git could not read the requested repository or revision.")
    return result.stdout


def github_url(remote: str | None) -> str | None:
    """Recognize GitHub URLs, stripping credentials instead of reproducing them."""
    if not remote:
        return None
    remote = remote.strip()
    if remote.startswith("git@github.com:"):
        path = remote[len("git@github.com:"):]
    else:
        parsed = urlsplit(remote)
        if parsed.scheme not in ("https", "ssh") or parsed.hostname != "github.com":
            return None
        path = parsed.path.lstrip("/")
    path = path.removesuffix(".git").rstrip("/")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", path):
        return None
    return "https://github.com/" + path


def markdown(text: str) -> str:
    # Commit subjects are data, including shell syntax and HTML.
    text = "".join(c if ord(c) >= 32 and ord(c) != 127 else " " for c in text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"([\\`*_\[\]{}|])", r"\\\1", text)


def category(subject: str) -> str:
    conventional = re.match(r"^([A-Za-z]+)(?:\([^\r\n)]*\))?!?:\s*(.*)$", subject)
    if conventional:
        kind, message = conventional.groups()
        kind = kind.lower()
        if kind in ("feat", "feature", "add"):
            return "Added"
        if kind in ("fix", "bugfix", "hotfix"):
            return "Fixed"
        if kind in ("remove", "delete", "drop"):
            return "Removed"
        # Conventional projects often encode removal as chore/refactor.
        if kind in ("chore", "refactor") and re.match(
            r"^(remove|delete|drop)\b", message, re.I
        ):
            return "Removed"
        return "Changed"
    if re.match(r"^(add|adds|added|introduce|introduces)\b", subject, re.I):
        return "Added"
    if re.match(r"^(fix|fixes|fixed|repair|resolve|resolves)\b", subject, re.I):
        return "Fixed"
    if re.match(r"^(remove|removes|removed|delete|drop|drops)\b", subject, re.I):
        return "Removed"
    return "Changed"


def generate(repo: Path, since: str | None = None) -> str:
    head = (git(repo, "rev-parse", "--verify", "HEAD^{commit}") or "").strip()
    if (git(repo, "rev-parse", "--is-shallow-repository") or "").strip() == "true":
        raise ChangelogError(
            "Shallow history may omit releases. Fetch full history and tags first "
            "(git fetch --unshallow --tags), then retry."
        )
    if since is not None:
        if not since or since.startswith("-"):
            raise ChangelogError("--since must be a Git revision, not an option.")
        base = (git(repo, "rev-parse", "--verify", since + "^{commit}") or "").strip()
        label = since
    else:
        tag = git(repo, "describe", "--tags", "--abbrev=0", head, optional=True)
        label = tag.strip() if tag else None
        base = (
            (git(repo, "rev-parse", "--verify", "refs/tags/" + label + "^{commit}") or "").strip()
            if label else None
        )
    if base is not None:
        # An unrelated or future tag must not silently select an unintended range.
        git(repo, "merge-base", "--is-ancestor", base, head)
    revision_range = base + ".." + head if base else head
    raw = git(repo, "log", "--reverse", "--topo-order", "--format=%H%x00%s", revision_range, "--")
    origin = github_url(git(repo, "config", "--get", "remote.origin.url", optional=True))
    groups: dict[str, list[str]] = {name: [] for name in CATEGORIES}
    for record in (raw or "").rstrip("\n").split("\n") if raw else []:
        commit, separator, subject = record.partition("\0")
        if not separator or not re.fullmatch(r"[0-9a-f]{40,64}", commit):
            raise ChangelogError("Unexpected Git log record; no file was written.")
        reference = (
            f"[{commit[:10]}]({origin}/commit/{commit})" if origin else f"`{commit[:10]}`"
        )
        groups[category(subject)].append(f"- {markdown(subject)} ({reference})")
    boundary = f"since tag/revision **{markdown(label)}**" if label else "from the first commit (no reachable tag)"
    lines = [START, "## [Unreleased]", "", f"Generated {boundary}, through `{head}`.", ""]
    if base:
        lines += [f"Base commit: `{base}`.", ""]
    for name in CATEGORIES:
        lines += ["### " + name, ""]
        lines += groups[name] or ["_None._"]
        lines += [""]
    lines += [END, ""]
    return "\n".join(lines)


def merge_document(existing: str | None, block: str) -> str:
    if existing is None:
        return "# Changelog\n\n" + block
    if existing.count(START) != 1 or existing.count(END) != 1:
        raise ChangelogError(
            "Existing file is not a uniquely marked generated changelog. "
            "Use --stdout or choose a new --output path; existing content is preserved."
        )
    start, end = existing.index(START), existing.index(END)
    if (end < start or (start > 0 and existing[start - 1] != "\n")
            or existing[start + len(START):start + len(START) + 1] not in ("\r", "\n")
            or existing[end - 1:end] != "\n"):
        raise ChangelogError("Malformed generated section markers; file preserved.")
    tail = end + len(END)
    if tail < len(existing) and existing[tail] not in "\r\n":
        raise ChangelogError("Malformed end marker; file preserved.")
    newline = "\r\n" if "\r\n" in existing else "\n"
    # Replace only the owned section, retaining surrounding manual release notes.
    return existing[:start] + block.rstrip("\n").replace("\n", newline) + existing[tail:]


def write_output(path: Path, block: str, check: bool = False) -> int:
    if path.is_symlink():
        raise ChangelogError("Refusing to replace a symbolic link; choose a regular output file.")
    old = path.read_bytes() if path.exists() else None
    content = merge_document(old.decode("utf-8") if old is not None else None, block).encode("utf-8")
    if old == content:
        return 0
    if check:
        return 1
    # Write in the destination directory, then atomically replace the destination.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".changelog-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        if old is not None and path.read_bytes() != old:
            raise ChangelogError("Output changed during generation; refusing to overwrite it.")
        if old is None and path.exists():
            raise ChangelogError("Output appeared during generation; refusing to overwrite it.")
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repository (default: current directory)")
    parser.add_argument("--since", help="Override the nearest reachable tag with an ancestor revision")
    parser.add_argument("--output", type=Path, help="Output file (default: repository root/CHANGELOG.md)")
    parser.add_argument("--stdout", action="store_true", help="Preview without writing a file")
    parser.add_argument("--check", action="store_true", help="Exit 1 if output would change; never write")
    args = parser.parse_args(argv)
    if args.stdout and (args.output or args.check):
        parser.error("--stdout cannot be combined with --output or --check")
    try:
        root = Path((git(args.repo, "rev-parse", "--show-toplevel") or "").strip())
        block = generate(root, args.since)
        if args.stdout:
            sys.stdout.write("# Changelog\n\n" + block)
            return 0
        return write_output(args.output or root / "CHANGELOG.md", block, args.check)
    except (ChangelogError, OSError, UnicodeError, ValueError) as exc:
        print(f"changelog: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
