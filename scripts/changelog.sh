#!/usr/bin/env bash
# Generate CHANGELOG.md from git history since the latest tag.
set -euo pipefail

REPO_ROOT="${1:-.}"
cd "$REPO_ROOT"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh: not a git repository: $REPO_ROOT" >&2
  exit 1
fi

python3 - "$REPO_ROOT" <<'PY'
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
else:
    rev_range = "HEAD"
    version = "Unreleased"

log = subprocess.check_output(
    ["git", "log", rev_range, "--pretty=format:%s"],
    cwd=root,
    text=True,
)
subjects = [line for line in log.splitlines() if line.strip()]

buckets = {
    "Added": [],
    "Fixed": [],
    "Changed": [],
    "Removed": [],
    "Security": [],
    "Other": [],
}

def bucket_for(subject: str) -> str:
    s = subject.lower()
    if s.startswith(("feat:", "feat(", "feat!")):
        return "Added"
    if s.startswith(("fix:", "fix(", "fix!")):
        return "Fixed"
    if s.startswith(
        (
            "chore:", "chore(", "refactor:", "refactor(", "perf:", "perf(",
            "style:", "style(", "build:", "build(", "ci:", "ci(",
        )
    ):
        return "Changed"
    if s.startswith(("remove:", "remove(", "revert:", "revert(")):
        return "Removed"
    if s.startswith(("security:", "security(", "security!")):
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
print(f"Wrote CHANGELOG.md ({len(lines)} lines, range: {rev_range or 'all commits'})")
PY
