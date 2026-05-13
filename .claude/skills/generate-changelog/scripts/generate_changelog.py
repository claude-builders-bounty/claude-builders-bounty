#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


class CommandError(RuntimeError):
    pass


def _run(cmd: list[str], *, cwd: Optional[str] = None) -> str:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise CommandError(
            f"Command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def _try_run(cmd: list[str], *, cwd: Optional[str] = None) -> Optional[str]:
    try:
        return _run(cmd, cwd=cwd)
    except CommandError:
        return None


def _repo_root() -> Path:
    out = _run(["git", "rev-parse", "--show-toplevel"])
    return Path(out)


def _last_tag() -> Optional[str]:
    tag = _try_run(["git", "describe", "--tags", "--abbrev=0"])
    if not tag:
        return None
    return tag.strip()


def _commit_subjects(rev_range: str) -> list[str]:
    # Keep it deterministic and avoid merges (often noisy).
    out = _run(
        [
            "git",
            "log",
            "--no-merges",
            "--pretty=format:%s",
            rev_range,
        ]
    )
    subjects = [line.strip() for line in out.splitlines() if line.strip()]
    # Reverse to chronological order for nicer changelogs.
    subjects.reverse()
    return subjects


_CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?:\\((?P<scope>[^)]+)\\))?(?P<breaking>!)?:\\s+(?P<msg>.+)$"
)


def _strip_prefix(subject: str) -> str:
    m = _CONVENTIONAL_RE.match(subject)
    if not m:
        return subject
    return m.group("msg").strip()


def _classify(subject: str) -> str:
    s = subject.strip()
    lower = s.lower()

    m = _CONVENTIONAL_RE.match(s)
    if m:
        t = m.group("type").lower()
        if t in {"feat", "feature"}:
            return "Added"
        if t in {"fix", "bugfix", "hotfix"}:
            return "Fixed"
        if t in {"remove", "rm"}:
            return "Removed"
        if t in {"refactor", "perf", "build", "ci", "chore", "docs", "style", "test"}:
            return "Changed"
        # Unknown conventional type: default to Changed
        return "Changed"

    # Heuristic fallback for non-conventional messages.
    if lower.startswith(("add ", "added ", "introduce ", "implement ", "create ", "support ")):
        return "Added"
    if lower.startswith(("remove ", "removed ", "delete ", "drop ")):
        return "Removed"
    if any(k in lower for k in ("fix", "bug", "error", "typo", "crash", "panic")):
        return "Fixed"
    return "Changed"


@dataclass(frozen=True)
class Changelog:
    date: str
    since: Optional[str]
    added: list[str]
    fixed: list[str]
    changed: list[str]
    removed: list[str]

    def render(self) -> str:
        lines: list[str] = []
        lines.append("# Changelog")
        lines.append("")
        lines.append(f"## [Unreleased] - {self.date}")
        lines.append("")

        def section(title: str, items: Iterable[str]) -> None:
            items = list(items)
            lines.append(f"### {title}")
            if not items:
                lines.append("- (none)")
            else:
                for item in items:
                    lines.append(f"- {item}")
            lines.append("")

        section("Added", self.added)
        section("Fixed", self.fixed)
        section("Changed", self.changed)
        section("Removed", self.removed)

        return "\n".join(lines).rstrip() + "\n"


def build_changelog(*, since_tag: Optional[str]) -> Changelog:
    today = _dt.date.today().isoformat()
    rev_range = f"{since_tag}..HEAD" if since_tag else "HEAD"
    subjects = _commit_subjects(rev_range)

    buckets: dict[str, list[str]] = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}

    seen: set[str] = set()
    for subject in subjects:
        msg = _strip_prefix(subject)
        # Deduplicate exact lines to reduce noise.
        if msg in seen:
            continue
        seen.add(msg)
        buckets[_classify(subject)].append(msg)

    return Changelog(
        date=today,
        since=since_tag,
        added=buckets["Added"],
        fixed=buckets["Fixed"],
        changed=buckets["Changed"],
        removed=buckets["Removed"],
    )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    p.add_argument(
        "--since",
        dest="since",
        default=None,
        help="Git tag to start from (default: last tag). Use empty string to force full history.",
    )
    p.add_argument(
        "--output",
        dest="output",
        default="CHANGELOG.md",
        help="Output file path (default: CHANGELOG.md).",
    )
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)

    try:
        root = _repo_root()
    except CommandError as e:
        print(str(e), file=sys.stderr)
        return 2

    os.chdir(root)

    since_tag: Optional[str]
    if args.since == "":
        since_tag = None
    elif args.since:
        since_tag = args.since
    else:
        since_tag = _last_tag()

    try:
        changelog = build_changelog(since_tag=since_tag)
    except CommandError as e:
        print(str(e), file=sys.stderr)
        return 2

    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = root / out_path

    out_path.write_text(changelog.render(), encoding="utf-8")

    print(f"Wrote {out_path}")
    print(f"Range: {since_tag}..HEAD" if since_tag else "Range: full history")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

