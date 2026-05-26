#!/usr/bin/env bash
# Generate CHANGELOG.md from git history since the latest tag.
set -euo pipefail

REPO_ROOT="${1:-.}"
cd "$REPO_ROOT"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh: not a git repository: $REPO_ROOT" >&2
  exit 1
fi

PYTHON=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1 && python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 0) else 1)' 2>/dev/null; then
  PYTHON=python
else
  echo "changelog.sh: python3 (or python 3.x) is required but not found in PATH" >&2
  exit 1
fi

"$PYTHON" - "$REPO_ROOT" <<'PY'
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(sys.argv[1])
latest_tag = ""
try:
    latest_tag = subprocess.check_output(
        ["git", "describe", "--tags", "--abbrev=0"],
        cwd=root,
        text=True,
    ).strip()
except subprocess.CalledProcessError:
    pass

if latest_tag:
    rev_range = f"{latest_tag}..HEAD"
    version = latest_tag.lstrip("v")
    range_label = rev_range
else:
    rev_range = ""
    version = "Unreleased"
    range_label = "all commits"

log_cmd = ["git", "log", "--pretty=format:%s"]
if rev_range:
    log_cmd.insert(2, rev_range)

log = subprocess.check_output(log_cmd, cwd=root, text=True)
subjects = [line for line in log.splitlines() if line.strip()]

buckets = {
    "Added": [],
    "Fixed": [],
    "Changed": [],
    "Removed": [],
    "Security": [],
    "Other": [],
}


def commit_type(subject: str):
    m = re.match(r"^([a-z]+)(!)?[:(]", subject.lower())
    return m.group(1) if m else None


def bucket_for(subject: str) -> str:
    t = commit_type(subject)
    if t == "feat":
        return "Added"
    if t == "fix":
        return "Fixed"
    if t in ("chore", "refactor", "perf", "style", "build", "ci", "docs", "test"):
        return "Changed"
    if t in ("remove", "revert"):
        return "Removed"
    if t == "security":
        return "Security"
    return "Other"


for subject in subjects:
    buckets[bucket_for(subject)].append(subject)

today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
lines = ["# Changelog", "", f"## [{version}] - {today}", ""]
for title, items in buckets.items():
    if not items:
        continue
    lines.append(f"### {title}")
    lines.append("")
    lines.extend(f"- {item}" for item in items)
    lines.append("")

out = root / "CHANGELOG.md"
out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
print(f"Wrote CHANGELOG.md ({len(lines)} lines, range: {range_label})")
PY
