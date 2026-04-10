#!/usr/bin/env bash
# generate-changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage:
#   bash generate-changelog.sh [--since <ref>] [--output <file>]
#
# Options:
#   --since <ref>   Generate changelog since <ref> (tag, commit, date).
#                   Defaults to the most recent git tag.
#   --output <file> Output file path. Defaults to CHANGELOG.md.
#   --help         Show this help message.
#
# Requirements:
#   - git
#   - awk, grep, sed (standard Unix tools)
#
# Exit codes:
#   0  Success
#   1  No tags found / no commits since tag
#   2  Missing dependencies

set -euo pipefail

# ── Defaults ────────────────────────────────────────────────────────────────
SINCE_REF=""
OUTPUT_FILE="CHANGELOG.md"
TEMP_DIR=""
HDR="
\`\`\`\n
# Changelog\n
All notable changes to this project will be documented in this file.\n
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n
\`\`\`\n"

# ── Helpers ─────────────────────────────────────────────────────────────────
usage() {
  grep "^#" <"$0" | sed 's/^# //; s/^#//'
}

info()  { echo "[INFO]  $*" >&2; }
warn()  { echo "[WARN]  $*" >&2; }
error() { echo "[ERROR] $*" >&2; exit 1; }

cleanup() {
  if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
    rm -rf "$TEMP_DIR"
  fi
}
trap cleanup EXIT

# Check dependencies
check_deps() {
  for cmd in git awk grep sed; do
    command -v "$cmd" >/dev/null 2>&1 || error "Missing required command: $cmd"
  done
}

# ── Argument parsing ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since)  SINCE_REF="$2"; shift 2 ;;
    --output) OUTPUT_FILE="$2"; shift 2 ;;
    --help)   usage; exit 0 ;;
    *)        error "Unknown option: $1 (use --help)" ;;
  esac
done

check_deps

# ── Resolve base ref ────────────────────────────────────────────────────────
if [[ -z "$SINCE_REF" ]]; then
  # Find the most recent tag
  SINCE_REF=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -z "$SINCE_REF" ]]; then
    error "No git tags found. Use --since to specify a starting point."
  fi
  info "Using most recent tag as base: $SINCE_REF"
fi

# Verify the ref exists
git rev-parse "$SINCE_REF" >/dev/null 2>&1 || error "Invalid git ref: $SINCE_REF"

# ── Category detection ───────────────────────────────────────────────────────
# Maps conventional-commit prefixes to changelog sections.
declare -A SECTIONS=(
  [feat]="Added"
  [feat!]="Added"
  [fix]="Fixed"
  [fix!]="Fixed"
  [refactor]="Changed"
  [perf]="Changed"
  [perf!]="Changed"
  [chore]="Changed"
  [docs]="Changed"
  [test]="Changed"
  [ci]="Changed"
  [build]="Changed"
  [deps]="Changed"
  [breaking]="Breaking"
  [breaking!]="Breaking"
)

# Fallback section for unknown prefixes.
FALLBACK="Changed"

# ── Collect commits ──────────────────────────────────────────────────────────
info "Collecting commits from $SINCE_REF to HEAD..."

# Get commits in reverse chronological order (newest first).
# Format: scope|type|subject|short_hash|full_hash|author|date|body
commits=$(git log "$SINCE_REF..HEAD" \
  --pretty=format:"%s|(%h)|%H|%an|%aI|%b" \
  --no-merges \
  --reverse 2>/dev/null || true)

if [[ -z "$commits" ]]; then
  info "No commits found between $SINCE_REF and HEAD. Nothing to do."
  exit 0
fi

# ── Categorize ───────────────────────────────────────────────────────────────
declare -A buckets
buckets["Added"]=""
buckets["Fixed"]=""
buckets["Changed"]=""
buckets["Removed"]=""
buckets["Breaking"]=""

while IFS='|' read -r subject hash full_hash author date body; do
  # Skip empty lines
  [[ -z "$subject" ]] && continue

  # Extract conventional-commit type (first word before : or !)
  type_part="${subject%%[!:]*}"   # everything before first : or !
  type_part="${type_part%%!*}"    # strip any ! suffix

  # Map to section
  section="${SECTIONS[$type_part]:-$FALLBACK}"

  # Extract scope (word in parentheses, if present)
  if [[ "$subject" =~ ^([a-z]+)!?:\ (.*) ]]; then
    type="${BASH_REMATCH[1]}"
    rest="${BASH_REMATCH[2]}"
    if [[ "$rest" =~ \(([^)]+)\)\  ]]; then
      scope="**${BASH_REMATCH[1]}**: "
    else
      scope=""
    fi
    desc="$scope${rest}"
  elif [[ "$subject" =~ ^([a-z]+)!?:\ (.*) ]]; then
    type="${BASH_REMATCH[1]}"
    desc="${BASH_REMATCH[2]}"
  else
    # Non-conventional commit — use subject as-is under Changed
    section="$FALLBACK"
    type="misc"
    desc="$subject"
  fi

  # Detect Breaking Changes from body (either "BREAKING CHANGE:" or "!" in type)
  if [[ "$subject" =~ ! ]] || grep -qi "breaking.change" <<<"$body"; then
    section="Breaking"
  fi

  # Detect removals
  if [[ "$subject" =~ ^feat\(.*\):\ .*|fix\(.*\):\ .* ]]; then
    :
  fi
  if grep -qi "^removal\|^- " <<<"$body"; then
    section="Removed"
  fi

  short_hash="${hash}"
  entry="  - $desc ([\`$short_hash\`](#$full_hash))"

  buckets[$section]="${buckets[$section]}\n${entry}"

done <<< "$commits"

# ── Build output ─────────────────────────────────────────────────────────────
{
  # Header
  printf "%s\n" "$HDR"

  # Version + date line
  today=$(date "+%Y-%m-%d")
  version_line="## [$today]"
  if [[ -n "$SINCE_REF" ]]; then
    version_line+=" (from $SINCE_REF)"
  fi
  printf "%s\n" "$version_line"

  # Sections (skip empty ones)
  for section in Added Fixed Changed Removed Breaking; do
    content="${buckets[$section]}"
    if [[ -n "$content" ]]; then
      printf "\n### %s\n%s\n" "$section" "$content"
    fi
  done

  printf "\n---\n*Generated by generate-changelog.sh*\n"

} > "$OUTPUT_FILE"

info "CHANGELOG written to $OUTPUT_FILE"
