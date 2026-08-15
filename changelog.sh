#!/usr/bin/env bash
# ==============================================================================
# changelog.sh — Generate a structured Keep a Changelog CHANGELOG.md from git
# ==============================================================================

set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
SINCE_REF=""
UNTIL_REF="HEAD"
RELEASE_VERSION=""
DRY_RUN=false
PREPEND=true

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  -o, --output <file>     Target output file (default: CHANGELOG.md)
  -s, --since <ref>       Start git revision/tag (default: latest tag, or root if no tags)
  -u, --until <ref>       End git revision/tag (default: HEAD)
  -v, --version <name>    Release version title (default: 'Unreleased' or tag name)
  --dry-run               Print to stdout instead of modifying file
  --overwrite             Overwrite CHANGELOG.md instead of prepending
  -h, --help              Show this help message

Examples:
  bash changelog.sh
  bash changelog.sh --version "v1.2.0"
  bash changelog.sh --since "v1.0.0" --until "v1.1.0" -o CHANGELOG.md
EOF
  exit 0
}

# Parse CLI arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    -s|--since)
      SINCE_REF="$2"
      shift 2
      ;;
    -u|--until)
      UNTIL_REF="$2"
      shift 2
      ;;
    -v|--version)
      RELEASE_VERSION="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --overwrite)
      PREPEND=false
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      ;;
  esac
done

# Verify git repository
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: Current directory is not a git repository." >&2
  exit 1
fi

# Detect starting reference if not specified
if [[ -z "$SINCE_REF" ]]; then
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -n "$LATEST_TAG" ]]; then
    SINCE_REF="$LATEST_TAG"
  fi
fi

# Determine commit range
if [[ -n "$SINCE_REF" ]]; then
  COMMIT_RANGE="${SINCE_REF}..${UNTIL_REF}"
  RANGE_LABEL="${SINCE_REF} → ${UNTIL_REF}"
else
  COMMIT_RANGE="${UNTIL_REF}"
  RANGE_LABEL="Initial commit → ${UNTIL_REF}"
fi

# Determine release version header
TODAY=$(date +"%Y-%m-%d")
if [[ -z "$RELEASE_VERSION" ]]; then
  if [[ -n "$SINCE_REF" && "$UNTIL_REF" != "HEAD" ]]; then
    RELEASE_VERSION="$UNTIL_REF"
  else
    RELEASE_VERSION="Unreleased"
  fi
fi

# Temporary directory for processing
TMP_DIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'changelog')
trap 'rm -rf "$TMP_DIR"' EXIT

ADDED_FILE="$TMP_DIR/added.txt"
FIXED_FILE="$TMP_DIR/fixed.txt"
CHANGED_FILE="$TMP_DIR/changed.txt"
REMOVED_FILE="$TMP_DIR/removed.txt"
BREAKING_FILE="$TMP_DIR/breaking.txt"

touch "$ADDED_FILE" "$FIXED_FILE" "$CHANGED_FILE" "$REMOVED_FILE" "$BREAKING_FILE"

# Extract commits using null-separated records to safely handle multi-line bodies
# Each commit is: HASH\x1fSUBJECT\x1fAUTHOR\x1fBODY\x00
export COMMIT_RANGE TMP_DIR

python3 - <<'PYEOF'
import os
import re
import subprocess

commit_range = os.environ.get("COMMIT_RANGE", "HEAD")
tmp_dir = os.environ.get("TMP_DIR", "/tmp")

added_file = os.path.join(tmp_dir, "added.txt")
fixed_file = os.path.join(tmp_dir, "fixed.txt")
changed_file = os.path.join(tmp_dir, "changed.txt")
removed_file = os.path.join(tmp_dir, "removed.txt")
breaking_file = os.path.join(tmp_dir, "breaking.txt")

cmd = ["git", "log", commit_range, "--no-merges", "--format=%h%x1f%s%x1f%an%x1f%b%x00"]
try:
    output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8", errors="replace")
except subprocess.CalledProcessError:
    # If range is empty or invalid, fallback to last 50
    try:
        output = subprocess.check_output(["git", "log", "-n", "50", "--no-merges", "--format=%h%x1f%s%x1f%an%x1f%b%x00"], stderr=subprocess.DEVNULL).decode("utf-8", errors="replace")
    except Exception:
        output = ""

entries = output.split("\x00")

def format_entry(hash_str, desc, author):
    # Ensure nice commit markdown formatting
    desc = desc.strip()
    author = author.strip()
    if author:
        return f"- {desc} ([{hash_str}](https://github.com/commit/{hash_str})) - @{author}\n"
    else:
        return f"- {desc} ([{hash_str}](https://github.com/commit/{hash_str}))\n"

breaking_list = []
added_list = []
fixed_list = []
changed_list = []
removed_list = []

for entry in entries:
    if not entry.strip():
        continue
    parts = entry.split("\x1f")
    if len(parts) < 3:
        continue
    
    commit_hash = parts[0].strip()
    subject = parts[1].strip()
    author = parts[2].strip()
    body = parts[3].strip() if len(parts) > 3 else ""
    
    # Check for breaking change
    is_breaking = False
    if "BREAKING CHANGE:" in body or "BREAKING-CHANGE:" in body:
        is_breaking = True
    if re.search(r'^[a-zA-Z]+(\([^)]+\))?!:', subject):
        is_breaking = True
        
    # Clean description from conventional prefix
    # Matches: feat(scope)!: or feat: or fix(scope): etc.
    clean_desc = re.sub(r'^[a-zA-Z]+(\([^)]+\))?!*:\s*', '', subject, flags=re.IGNORECASE).strip()
    if not clean_desc:
        clean_desc = subject

    if is_breaking:
        breaking_list.append(f"- **BREAKING**: {clean_desc} ([{commit_hash}](https://github.com/commit/{commit_hash}))\n")

    # Categorization logic
    lower_subj = subject.lower()
    
    if re.match(r'^(feat|feature|add)(\([^)]+\))?!*:', lower_subj):
        added_list.append(format_entry(commit_hash, clean_desc, author))
    elif re.match(r'^(fix|bug|patch|hotfix)(\([^)]+\))?!*:', lower_subj):
        fixed_list.append(format_entry(commit_hash, clean_desc, author))
    elif re.match(r'^(remove|removed|delete|deleted|revert|deprecate|deprecated)(\([^)]+\))?!*:', lower_subj):
        removed_list.append(format_entry(commit_hash, clean_desc, author))
    elif re.match(r'^(refactor|perf|performance|chore|style|build|ci|docs|test|update|types)(\([^)]+\))?!*:', lower_subj):
        changed_list.append(format_entry(commit_hash, clean_desc, author))
    else:
        # Fallback keywords
        if any(k in lower_subj for k in ['add', 'feature', 'support', 'implement', 'initial']):
            added_list.append(format_entry(commit_hash, clean_desc, author))
        elif any(k in lower_subj for k in ['fix', 'bug', 'issue', 'resolve', 'crash', 'patch']):
            fixed_list.append(format_entry(commit_hash, clean_desc, author))
        elif any(k in lower_subj for k in ['remove', 'delete', 'drop', 'revert', 'deprecated']):
            removed_list.append(format_entry(commit_hash, clean_desc, author))
        else:
            changed_list.append(format_entry(commit_hash, clean_desc, author))

with open(breaking_file, "w", encoding="utf-8") as f:
    f.writelines(breaking_list)
with open(added_file, "w", encoding="utf-8") as f:
    f.writelines(added_list)
with open(fixed_file, "w", encoding="utf-8") as f:
    f.writelines(fixed_list)
with open(changed_file, "w", encoding="utf-8") as f:
    f.writelines(changed_list)
with open(removed_file, "w", encoding="utf-8") as f:
    f.writelines(removed_list)
PYEOF

# Generate new release markdown block
RELEASE_MD="$TMP_DIR/release.md"
cat <<EOF > "$RELEASE_MD"
## [${RELEASE_VERSION}] - ${TODAY}

EOF

has_content=false

if [[ -s "$BREAKING_FILE" ]]; then
  has_content=true
  echo "### ⚠️ Breaking Changes" >> "$RELEASE_MD"
  cat "$BREAKING_FILE" >> "$RELEASE_MD"
  echo "" >> "$RELEASE_MD"
fi

if [[ -s "$ADDED_FILE" ]]; then
  has_content=true
  echo "### Added" >> "$RELEASE_MD"
  cat "$ADDED_FILE" >> "$RELEASE_MD"
  echo "" >> "$RELEASE_MD"
fi

if [[ -s "$CHANGED_FILE" ]]; then
  has_content=true
  echo "### Changed" >> "$RELEASE_MD"
  cat "$CHANGED_FILE" >> "$RELEASE_MD"
  echo "" >> "$RELEASE_MD"
fi

if [[ -s "$FIXED_FILE" ]]; then
  has_content=true
  echo "### Fixed" >> "$RELEASE_MD"
  cat "$FIXED_FILE" >> "$RELEASE_MD"
  echo "" >> "$RELEASE_MD"
fi

if [[ -s "$REMOVED_FILE" ]]; then
  has_content=true
  echo "### Removed" >> "$RELEASE_MD"
  cat "$REMOVED_FILE" >> "$RELEASE_MD"
  echo "" >> "$RELEASE_MD"
fi

if ! $has_content; then
  echo "_No notable changes in this release range (${RANGE_LABEL})._" >> "$RELEASE_MD"
  echo "" >> "$RELEASE_MD"
fi

# Assemble complete CHANGELOG
FINAL_MD="$TMP_DIR/final.md"

HEADER_CONTENT="# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"

if [[ -f "$OUTPUT_FILE" && "$PREPEND" = true ]]; then
  # Strip old header if present
  EXISTING_BODY=$(sed -e '/^# Changelog/d' -e '/^All notable changes/d' -e '/^The format is based/d' -e '/^and this project adheres/d' "$OUTPUT_FILE" | sed -e '/./,$!d')
  
  echo "$HEADER_CONTENT" > "$FINAL_MD"
  cat "$RELEASE_MD" >> "$FINAL_MD"
  if [[ -n "$EXISTING_BODY" ]]; then
    echo "$EXISTING_BODY" >> "$FINAL_MD"
  fi
else
  echo "$HEADER_CONTENT" > "$FINAL_MD"
  cat "$RELEASE_MD" >> "$FINAL_MD"
fi

if $DRY_RUN; then
  cat "$FINAL_MD"
else
  cp "$FINAL_MD" "$OUTPUT_FILE"
  echo "✓ Successfully generated ${OUTPUT_FILE} (${RELEASE_VERSION} - ${RANGE_LABEL})"
fi
