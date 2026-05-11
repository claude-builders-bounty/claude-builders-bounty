#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history
# Bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1
set -euo pipefail

REPO_DIR="${1:-.}"
cd "$REPO_DIR"

# Ensure we're in a git repo
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "❌ Not a git repository" >&2
  exit 1
fi

# Get the repo URL for commit links
REPO_URL=$(git remote get-url origin 2>/dev/null | sed -E 's#(git@|https://)github.com[:/]##;s/\.git$//' || echo "")

# Find the last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -z "$LAST_TAG" ]; then
  COMMIT_RANGE="HEAD"
  VERSION="Unreleased"
else
  COMMIT_RANGE="${LAST_TAG}..HEAD"
  VERSION="Unreleased (since ${LAST_TAG})"
fi

# Use Python to do the heavy lifting (reliable cross-platform)
python3 << PY_EOF
import subprocess, re, os, datetime

last_tag = "${LAST_TAG}"
version = "${VERSION}"
repo_url = "${REPO_URL}"

# Get commits
if last_tag:
    result = subprocess.run(["git", "log", "--pretty=format:%H%x00%s", "--no-merges", f"{last_tag}..HEAD"], capture_output=True, text=True)
else:
    result = subprocess.run(["git", "log", "--pretty=format:%H%x00%s", "--no-merges"], capture_output=True, text=True)

if not result.stdout.strip():
    with open("CHANGELOG.md", "w") as f:
        f.write(f"# Changelog\n\nNo new commits since {last_tag}.\n")
    print("No new commits found.")
    exit(0)

categories = {"Added": [], "Fixed": [], "Changed": [], "Removed": [], "Other": []}

add_re = re.compile(r'^(add|added|adding|new|create|created|introduce|introduced|implement|implemented|support|feature|feat)', re.I)
fix_re = re.compile(r'^(fix|fixed|fixing|bug|patch|resolve|resolved|close|closed|repair|hotfix)', re.I)
change_re = re.compile(r'^(change|changed|changing|update|updated|updating|modify|modified|improve|improved|refactor|refactored|rename|renamed|move|moved|migrate|migrated|bump|build|chore|ci)', re.I)
remove_re = re.compile(r'^(remove|removed|removing|delete|deleted|deleting|drop|dropped|deprecate|deprecated|clean|cleanup)', re.I)

for line in result.stdout.strip().split("\n"):
    parts = line.split("\x00", 1)
    if len(parts) != 2:
        continue
    hash_val, msg = parts
    short = hash_val[:7]
    if repo_url:
        link = f"[{short}](https://github.com/{repo_url}/commit/{hash_val})"
    else:
        link = short
    
    entry = f"- {msg} ({link})"
    
    # Strip conventional commit prefix for categorization
    clean_msg = re.sub(r'^(feat|fix|refactor|chore|docs|style|test|build|ci|perf|revert)(\(.+\))?!?:\s*', '', msg)
    
    if add_re.match(clean_msg) or msg.startswith('feat'):
        categories["Added"].append(entry)
    elif fix_re.match(clean_msg) or msg.startswith('fix'):
        categories["Fixed"].append(entry)
    elif remove_re.match(clean_msg) or msg.startswith('revert'):
        categories["Removed"].append(entry)
    elif change_re.match(clean_msg) or any(msg.startswith(p) for p in ['refactor','chore','build','ci','docs','style','test','perf']):
        categories["Changed"].append(entry)
    else:
        categories["Other"].append(entry)

today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

lines = ["# Changelog", "", f"## {version} ({today})", ""]

for cat in ["Added", "Fixed", "Changed", "Removed", "Other"]:
    if categories[cat]:
        lines.append(f"### {cat}")
        lines.append("")
        lines.extend(categories[cat])
        lines.append("")

# Append old changelog
old_content = ""
if os.path.exists("CHANGELOG.md"):
    with open("CHANGELOG.md") as f:
        old = f.read()
    # Skip the header and first section
    sections = old.split("\n## ")
    if len(sections) > 1:
        old_content = "\n## ".join(sections[1:])

if old_content.strip():
    lines.append(old_content.rstrip())

with open("CHANGELOG.md", "w") as f:
    f.write("\n".join(lines) + "\n")

total = sum(len(v) for v in categories.values())
counts = {k: len(v) for k, v in categories.items() if v}
parts = [f"{v} {k.lower()}" for k, v in counts.items()]
print(f"✅ CHANGELOG.md generated: {total} commits → {', '.join(parts)}")
PY_EOF
