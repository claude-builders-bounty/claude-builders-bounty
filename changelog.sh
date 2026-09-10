#!/usr/bin/env bash
set -e

# changelog.sh - Git Changelog Generator
# Generates a structured CHANGELOG.md from git commits since the last tag (or initial commit if no tag exists).

OUTPUT_FILE="${1:-CHANGELOG.md}"

# Ensure we are in a git repository
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: Not a git repository." >&2
    exit 1
fi

# Ensure there is at least one commit
if ! git rev-parse HEAD >/dev/null 2>&1; then
    echo "Error: No commits found in the repository." >&2
    exit 1
fi

# Determine commit range (since last tag or all commits if no tags exist)
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)

if [ -n "$LATEST_TAG" ]; then
    RANGE="${LATEST_TAG}..HEAD"
    TAG_INFO="since tag ${LATEST_TAG}"
else
    RANGE="HEAD"
    TAG_INFO="from initial commit"
fi

echo "Generating changelog ${TAG_INFO}..."

# Process commits and generate Markdown output
python3 - "$RANGE" "$OUTPUT_FILE" "$LATEST_TAG" << 'EOF'
import sys
import subprocess
import re
from datetime import date

range_arg = sys.argv[1]
output_file = sys.argv[2]
latest_tag = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None

# Get git log: hash|subject|author|date
cmd = ["git", "log", range_arg, "--pretty=format:%h|%s|%an|%ad", "--date=short"]
try:
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    raw_log = res.stdout.strip()
except subprocess.CalledProcessError as e:
    print(f"Error executing git log: {e}", file=sys.stderr)
    sys.exit(1)

commits = []
if raw_log:
    for line in raw_log.split("\n"):
        parts = line.split("|", 3)
        if len(parts) >= 2:
            commits.append({
                "hash": parts[0],
                "subject": parts[1],
                "author": parts[2] if len(parts) > 2 else "",
                "date": parts[3] if len(parts) > 3 else ""
            })

added = []
fixed = []
changed = []
removed = []

def categorize(subject):
    s_lower = subject.lower().strip()
    
    # Check conventional commit prefix first (e.g. feat:, fix(scope):, refactor!:)
    m = re.match(r'^([a-z]+)(?:\([^\)]+\))?!?:', s_lower)
    if m:
        prefix = m.group(1)
        if prefix in ['feat', 'add', 'new']:
            return 'added'
        if prefix in ['fix', 'bug', 'patch']:
            return 'fixed'
        if prefix in ['remove', 'deprecate', 'delete']:
            return 'removed'
        if prefix in ['refactor', 'update', 'change', 'chore', 'docs', 'style', 'perf', 'ci', 'test', 'build']:
            return 'changed'

    # Keyword / prefix search
    if re.search(r'^(feat|add|new|added|feature|create|created|initial)\b', s_lower) or re.search(r'\b(feat|add|new)\b', s_lower):
        return 'added'
    if re.search(r'^(fix|bug|patch|fixed|resolved)\b', s_lower) or re.search(r'\b(fix|bug|patch)\b', s_lower):
        return 'fixed'
    if re.search(r'^(remove|deprecate|delete|removed|deleted)\b', s_lower) or re.search(r'\b(remove|deprecate|delete)\b', s_lower):
        return 'removed'
    if re.search(r'^(refactor|update|change|chore|docs|style|perf|updated|changed)\b', s_lower) or re.search(r'\b(refactor|update|change)\b', s_lower):
        return 'changed'

    return 'changed'

for c in commits:
    subj = c["subject"]
    chash = c["hash"]
    cat = categorize(subj)
    entry = f"- {subj} (`{chash}`)"
    
    if cat == 'added':
        added.append(entry)
    elif cat == 'fixed':
        fixed.append(entry)
    elif cat == 'removed':
        removed.append(entry)
    else:
        changed.append(entry)

today = date.today().isoformat()
version_title = f"## [Unreleased] - {today}" if not latest_tag else f"## [Unreleased] (since {latest_tag}) - {today}"

sections = []
if added:
    sections.append("### Added\n" + "\n".join(added))
if fixed:
    sections.append("### Fixed\n" + "\n".join(fixed))
if changed:
    sections.append("### Changed\n" + "\n".join(changed))
if removed:
    sections.append("### Removed\n" + "\n".join(removed))

if not sections:
    sections.append("_No changes found since last release._")

changelog_body = f"{version_title}\n\n" + "\n\n".join(sections) + "\n"

header = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""

output_content = header + changelog_body

with open(output_file, "w") as f:
    f.write(output_content)

print(f"Changelog written to {output_file}")
EOF
