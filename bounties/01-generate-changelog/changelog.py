#!/usr/bin/env python3
"""Portable changelog generator (same rules as changelog.sh)."""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "CHANGELOG.md")
    try:
        root = run(["git", "rev-parse", "--show-toplevel"])
    except subprocess.CalledProcessError:
        print("error: not inside a git repository", file=sys.stderr)
        return 1

    try:
        last_tag = run(["git", "describe", "--tags", "--abbrev=0"])
        since = f"since {last_tag}"
        log_cmd = ["git", "log", f"{last_tag}..HEAD", "--pretty=format:%s"]
    except subprocess.CalledProcessError:
        last_tag = ""
        since = "full history (no tags found)"
        log_cmd = ["git", "log", "HEAD", "--pretty=format:%s"]

    try:
        subjects = [s for s in run(log_cmd).splitlines() if s.strip()]
    except subprocess.CalledProcessError:
        subjects = []

    buckets = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
    for s in subjects:
        low = s.lower()
        if re.match(r"^(feat|feature)(\(.+\))?:", low) or re.search(
            r"(^|\s)(add|added|adding|implement|introduce)", low
        ):
            buckets["Added"].append(s)
        elif re.match(r"^fix(\(.+\))?:", low) or re.search(
            r"(^|\s)(fix|fixed|fixes|bugfix|hotfix|patch)", low
        ):
            buckets["Fixed"].append(s)
        elif re.match(r"^(remove|revert|delete)(\(.+\))?:", low) or re.search(
            r"(^|\s)(remove|removed|delete|deleted|drop|dropped)", low
        ):
            buckets["Removed"].append(s)
        elif re.match(r"^(chore|refactor|perf|docs|style|build|ci)(\(.+\))?:", low) or re.search(
            r"(^|\s)(change|changed|update|updated|refactor|improve|bump)", low
        ):
            buckets["Changed"].append(s)
        else:
            buckets["Changed"].append(s)

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [f"# Changelog\n", f"Generated {date} ({since}).\n"]
    for title in ("Added", "Fixed", "Changed", "Removed"):
        lines.append(f"## {title}\n")
        items = buckets[title]
        if not items:
            lines.append("_None_\n")
        else:
            for i in items:
                lines.append(f"- {i}")
            lines.append("")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({since}, {len(subjects)} commit subjects).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
