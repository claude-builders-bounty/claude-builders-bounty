#!/usr/bin/env python3
"""Generate CHANGELOG.md from git history since the last tag."""
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run(*args, cwd: Path) -> str:
    r = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return ""
    return r.stdout.strip()


def categorize(subject: str) -> str:
    s = subject.lower()
    if re.match(r"^(fix|bug|patch)", s):
        return "Fixed"
    if re.match(r"^(remove|delete|drop)", s):
        return "Removed"
    if re.match(r"^(change|update|refactor|chore|docs)", s):
        return "Changed"
    return "Added"


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out = Path(sys.argv[2] if len(sys.argv) > 2 else root / "CHANGELOG.md")
    last_tag = run("git", "describe", "--tags", "--abbrev=0", cwd=root)
    if last_tag:
        log_range = f"{last_tag}..HEAD"
        since = f"Changes since {last_tag}"
        version = last_tag
    else:
        log_range = "HEAD"
        since = "Initial changelog"
        version = "Unreleased"

    raw = run("git", "log", log_range, "--pretty=format:%h: %s", cwd=root)
    if not raw:
        raw = run("git", "log", "--pretty=format:%h: %s", cwd=root)

    sections = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        subject = line.split(": ", 1)[-1] if ": " in line else line
        sections[categorize(subject)].append(line)

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = ["# Changelog", "", f"## {version} ({date})", "", since, ""]
    for name in ("Added", "Fixed", "Changed", "Removed"):
        if sections[name]:
            lines.append(f"### {name}")
            lines.extend(f"- {item}" for item in sections[name])
            lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
