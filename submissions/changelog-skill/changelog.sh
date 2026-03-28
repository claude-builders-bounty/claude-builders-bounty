#!/usr/bin/env bash
# changelog.sh — Generate a CHANGELOG.md from git history
# Follows Keep a Changelog (https://keepachangelog.com/en/1.1.0/)
#
# Usage:
#   ./changelog.sh                  # Auto-detect tag range, write CHANGELOG.md
#   ./changelog.sh --version 1.2.0  # Use a specific version header
#   ./changelog.sh --stdout          # Print to stdout instead of writing file
#   ./changelog.sh --help            # Show usage
#
# Compatible with Bash 3.2+ (macOS default) and GNU Bash 4+/5+.

set -euo pipefail

# ---------------------------------------------------------------------------
# Portable lowercase function (works on Bash 3.2)
# ---------------------------------------------------------------------------
to_lower() { echo "$1" | tr '[:upper:]' '[:lower:]'; }
to_upper_first() {
  local first rest
  first="$(echo "${1:0:1}" | tr '[:lower:]' '[:upper:]')"
  rest="${1:1}"
  echo "${first}${rest}"
}

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
VERSION_LABEL="Unreleased"
OUTPUT_FILE="CHANGELOG.md"
STDOUT_ONLY=false

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --version|-v)
      VERSION_LABEL="$2"; shift 2 ;;
    --output|-o)
      OUTPUT_FILE="$2"; shift 2 ;;
    --stdout)
      STDOUT_ONLY=true; shift ;;
    --help|-h)
      echo "Usage: changelog.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --version, -v VERSION   Set the version header (default: Unreleased)"
      echo "  --output, -o FILE       Output file path (default: CHANGELOG.md)"
      echo "  --stdout                Print to stdout instead of writing a file"
      echo "  --help, -h              Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# Verify we are inside a git repository
# ---------------------------------------------------------------------------
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Error: not inside a git repository." >&2
  exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"

# ---------------------------------------------------------------------------
# Determine commit range
# ---------------------------------------------------------------------------
LATEST_TAG=""
RANGE=""
RANGE_DESC="full history (no tags found)"
if LATEST_TAG="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  RANGE="${LATEST_TAG}..HEAD"
  RANGE_DESC="${LATEST_TAG} to HEAD"
fi

TODAY="$(date +%Y-%m-%d)"

# ---------------------------------------------------------------------------
# Collect commits
# Use NUL byte as record separator to handle multi-line bodies safely.
# We extract the subject (%s) and body (%b) separated by |||, then NUL.
# ---------------------------------------------------------------------------
DELIM='|||'

tmp_added="$(mktemp)"
tmp_fixed="$(mktemp)"
tmp_changed="$(mktemp)"
tmp_removed="$(mktemp)"
tmp_raw="$(mktemp)"
trap 'rm -f "$tmp_added" "$tmp_fixed" "$tmp_changed" "$tmp_removed" "$tmp_raw"' EXIT

# Fetch raw log with NUL-separated records
if [[ -n "$RANGE" ]]; then
  git log "$RANGE" --pretty=format:"%s${DELIM}%b%x00" --no-merges > "$tmp_raw" 2>/dev/null || true
else
  git log --pretty=format:"%s${DELIM}%b%x00" --no-merges > "$tmp_raw" 2>/dev/null || true
fi

skip_count=0
total_count=0

# Process NUL-separated records
while IFS= read -r -d '' record; do
  [[ -z "$record" ]] && continue

  # Subject is everything before the first |||
  subject="${record%%${DELIM}*}"
  body="${record#*${DELIM}}"

  # Trim whitespace and newlines from subject
  subject="$(echo "$subject" | tr -d '\n\r' | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')"
  [[ -z "$subject" ]] && continue

  # Skip merge commits
  if echo "$subject" | grep -qE '^Merge[d]? '; then
    skip_count=$((skip_count + 1))
    continue
  fi

  total_count=$((total_count + 1))

  # Detect breaking changes
  breaking=""
  if echo "$body" | grep -q "BREAKING CHANGE:" 2>/dev/null; then
    breaking="**BREAKING:** "
  fi

  # --- Categorize ---
  category=""
  display="$subject"

  # Try conventional commit pattern: type(scope)!: description
  if echo "$subject" | grep -qE '^[a-zA-Z]+(\(.*\))?(!)?: '; then
    cc_type="$(echo "$subject" | sed -E 's/^([a-zA-Z]+)(\(.*\))?(!)?: .*/\1/')"
    cc_type="$(to_lower "$cc_type")"
    display="$(echo "$subject" | sed -E 's/^[a-zA-Z]+(\(.*\))?(!)?: //')"

    # Check for ! in prefix
    if echo "$subject" | grep -qE '^[a-zA-Z]+(\(.*\))?!: '; then
      breaking="**BREAKING:** "
    fi

    case "$cc_type" in
      feat)     category="Added" ;;
      fix)      category="Fixed" ;;
      revert)   category="Removed" ;;
      refactor|perf|style|build|ci|chore|docs|test)
                category="Changed" ;;
    esac
  fi

  # Keyword fallback for non-conventional or unrecognized types
  if [[ -z "$category" ]]; then
    subj_lower="$(to_lower "$subject")"
    if echo "$subj_lower" | grep -qEi '(^|\W)(add|new|create|introduce|implement|support)(\W|$)'; then
      category="Added"
    elif echo "$subj_lower" | grep -qEi '(^|\W)(fix|bug|patch|resolve|close[sd]?|correct|repair)(\W|$)'; then
      category="Fixed"
    elif echo "$subj_lower" | grep -qEi '(^|\W)(remove|delete|drop|deprecate|strip|clean ?up)(\W|$)'; then
      category="Removed"
    else
      category="Changed"
    fi
  fi

  # Clean up display text
  display="$(echo "$display" | sed 's/^[[:space:]]*//')"
  if [[ -n "$display" ]]; then
    display="$(to_upper_first "$display")"
  fi
  # Remove trailing period
  display="${display%.}"

  entry="${breaking}${display}"

  case "$category" in
    Added)   echo "$entry" >> "$tmp_added" ;;
    Fixed)   echo "$entry" >> "$tmp_fixed" ;;
    Changed) echo "$entry" >> "$tmp_changed" ;;
    Removed) echo "$entry" >> "$tmp_removed" ;;
  esac

done < "$tmp_raw"

# ---------------------------------------------------------------------------
# Sort entries alphabetically and deduplicate within each category
# ---------------------------------------------------------------------------
for f in "$tmp_added" "$tmp_fixed" "$tmp_changed" "$tmp_removed"; do
  if [[ -s "$f" ]]; then
    sort -fu "$f" -o "$f"
  fi
done

count_lines() {
  if [[ -s "$1" ]]; then
    wc -l < "$1" | tr -d ' '
  else
    echo "0"
  fi
}

added_count="$(count_lines "$tmp_added")"
fixed_count="$(count_lines "$tmp_fixed")"
changed_count="$(count_lines "$tmp_changed")"
removed_count="$(count_lines "$tmp_removed")"

# ---------------------------------------------------------------------------
# Build the new release section
# ---------------------------------------------------------------------------
new_section="## [${VERSION_LABEL}] - ${TODAY}"$'\n'

append_section() {
  local header="$1"
  local file="$2"
  if [[ -s "$file" ]]; then
    new_section+=$'\n'"### ${header}"$'\n'
    while IFS= read -r entry; do
      [[ -n "$entry" ]] && new_section+="- ${entry}"$'\n'
    done < "$file"
  fi
}

append_section "Added"   "$tmp_added"
append_section "Fixed"   "$tmp_fixed"
append_section "Changed" "$tmp_changed"
append_section "Removed" "$tmp_removed"

# ---------------------------------------------------------------------------
# Build full CHANGELOG.md content
# ---------------------------------------------------------------------------
HEADER="# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
"

EXISTING_FILE="${REPO_ROOT}/${OUTPUT_FILE}"

if [[ -f "$EXISTING_FILE" ]]; then
  existing_body="$(sed -n '/^## /,$p' "$EXISTING_FILE")"
  if [[ -n "$existing_body" ]]; then
    full_content="${HEADER}
${new_section}
${existing_body}"
  else
    full_content="${HEADER}
${new_section}"
  fi
else
  full_content="${HEADER}
${new_section}"
fi

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
if $STDOUT_ONLY; then
  echo "$full_content"
else
  echo "$full_content" > "$EXISTING_FILE"
  echo "Wrote ${OUTPUT_FILE}" >&2
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo "" >&2
echo "--- Summary ---" >&2
echo "Range:   ${RANGE_DESC}" >&2
echo "Commits: ${total_count} processed, ${skip_count} merge commits skipped" >&2
echo "Added:   ${added_count}" >&2
echo "Fixed:   ${fixed_count}" >&2
echo "Changed: ${changed_count}" >&2
echo "Removed: ${removed_count}" >&2
