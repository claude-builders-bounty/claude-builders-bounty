#!/usr/bin/env bash
# changelog.sh — build a structured CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh [VERSION] [options]
#
# Options:
#   --stdout          print the new section instead of writing the file
#   --file <path>     output file (default: CHANGELOG.md)
#   --since <ref>     start after this ref (default: the last tag, else full history)
#   --all             also include maintenance commits (docs, chore, test, ci, build)
#   --hashes          append the short commit hash to every entry
#   -h, --help        show this help
#
# Commits are grouped into Added / Fixed / Changed / Removed using Conventional
# Commits prefixes, with keyword heuristics for plain messages. Breaking changes
# (!: / BREAKING CHANGE:) get their own block at the top of the section.
set -euo pipefail

OUT="CHANGELOG.md"
MODE="write"
SINCE=""
VERSION=""
INCLUDE_ALL=0
WITH_HASHES=0

usage() {
  cat <<'HELP'
changelog.sh — build a structured CHANGELOG.md from git history.

Usage:
  bash changelog.sh [VERSION] [options]

Options:
  --stdout          print the new section instead of writing the file
  --file <path>     output file (default: CHANGELOG.md)
  --since <ref>     start after this ref (default: the last tag, else full history)
  --all             also include maintenance commits (docs, chore, test, ci, build)
  --hashes          append the short commit hash to every entry
  -h, --help        show this help

Commits are grouped into Added / Fixed / Changed / Removed using Conventional
Commits prefixes, with keyword heuristics for plain messages. Breaking changes
(!: / BREAKING CHANGE:) get their own block at the top of the section.
HELP
}

while [ $# -gt 0 ]; do
  case "$1" in
    --stdout) MODE="stdout" ;;
    --file) OUT="${2:?--file needs a path}"; shift ;;
    --since) SINCE="${2:?--since needs a ref}"; shift ;;
    --all) INCLUDE_ALL=1 ;;
    --hashes) WITH_HASHES=1 ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    *) VERSION="$1" ;;
  esac
  shift
done

command -v git >/dev/null 2>&1 || { echo "git is not installed" >&2; exit 1; }
git rev-parse --git-dir >/dev/null 2>&1 || { echo "Not a git repository (run it from the project root)" >&2; exit 1; }

if [ -z "$SINCE" ]; then
  SINCE="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi
if [ -n "$SINCE" ]; then RANGE="$SINCE..HEAD"; else RANGE="HEAD"; fi
TITLE="${VERSION:-Unreleased}"
DATE_UTC="$(date -u +%Y-%m-%d)"

# Hash list of commits that declare a breaking change in the body.
BREAKING_HASHES="$(git log "$RANGE" --no-merges --grep='BREAKING CHANGE' --pretty=tformat:'%h' 2>/dev/null || true)"

section_for() {
  # Decide the bucket for a subject line. Empty means "do not list it".
  local subject="$1" lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  # "1.2.3" / "v1.2.3": a release commit, not a change.
  if printf '%s' "$lower" | grep -Eq '^v?[0-9]+\.[0-9]+\.[0-9]+$'; then
    if [ "$INCLUDE_ALL" = "1" ]; then echo "Changed"; else echo ""; fi
    return
  fi
  case "$lower" in
    feat*|feature*) echo "Added" ;;
    fix*|bugfix*|hotfix*) echo "Fixed" ;;
    remove*|delete*|drop*|revert*|deprecat*) echo "Removed" ;;
    refactor*|perf*|change*|update*|improve*|style*|tweak*) echo "Changed" ;;
    docs*|doc*|chore*|test*|tests*|ci*|build*|release*|bump*|deps*|dependenc*)
      if [ "$INCLUDE_ALL" = "1" ]; then echo "Changed"; else echo ""; fi ;;
    *)
      case "$lower" in
        *"add "*|*"added "*|*"new "*) echo "Added" ;;
        *fix*|*bug*) echo "Fixed" ;;
        *remov*|*delet*|*"drop "*|*deprecat*) echo "Removed" ;;
        *) echo "Changed" ;;
      esac ;;
  esac
}

format_entry() {
  local subject="$1" hash="$2" scope="" text
  if printf '%s' "$subject" | grep -Eq '^[A-Za-z]+\([^)]+\)!?:'; then
    scope="$(printf '%s' "$subject" | sed -E 's/^[A-Za-z]+\(([^)]+)\)!?:.*/\1/')"
  fi
  text="$(printf '%s' "$subject" | sed -E 's/^[A-Za-z]+(\([^)]+\))?!?:[[:space:]]*//')"
  case "$text" in
    [a-z]*) text="$(printf '%s' "$text" | awk '{print toupper(substr($0,1,1)) substr($0,2)}')" ;;
  esac
  [ -n "$scope" ] && text="**$scope:** $text"
  [ "$WITH_HASHES" = "1" ] && text="$text (\`$hash\`)"
  printf -- '- %s\n' "$text"
}

ADDED=""; FIXED=""; CHANGED=""; REMOVED=""; BREAKING=""; COUNT=0

while IFS=$'\t' read -r hash subject; do
  [ -n "${hash:-}" ] || continue
  case "$subject" in Merge*|"Merge pull"*|"Merge branch"*|"Merge remote"*) continue ;; esac
  BUCKET="$(section_for "$subject")"
  ENTRY="$(format_entry "$subject" "$hash")"
  if printf '%s\n' "$BREAKING_HASHES" | grep -qx "$hash" || printf '%s' "$subject" | grep -Eq '^[A-Za-z]+(\([^)]+\))?!:'; then
    BREAKING="$BREAKING$ENTRY"$'\n'
  fi
  COUNT=$((COUNT + 1))
  case "$BUCKET" in
    Added) ADDED="$ADDED$ENTRY"$'\n' ;;
    Fixed) FIXED="$FIXED$ENTRY"$'\n' ;;
    Changed) CHANGED="$CHANGED$ENTRY"$'\n' ;;
    Removed) REMOVED="$REMOVED$ENTRY"$'\n' ;;
    *) : ;;  # maintenance commit and --all was not passed
  esac
done < <(git log "$RANGE" --no-merges --pretty=tformat:'%h%x09%s')

# Each entry was accumulated with a trailing newline; drop the last one so the
# section does not end with a blank line.
BREAKING="${BREAKING%$'\n'}"
ADDED="${ADDED%$'\n'}"
FIXED="${FIXED%$'\n'}"
CHANGED="${CHANGED%$'\n'}"
REMOVED="${REMOVED%$'\n'}"

SECTION="## [$TITLE] - $DATE_UTC"
if [ -n "$SINCE" ]; then
  SECTION="$SECTION"$'\n\n'"<sub>Changes since \`$SINCE\`.</sub>"
fi
if [ -n "$BREAKING" ]; then SECTION="$SECTION"$'\n\n'"### Breaking changes"$'\n'"$BREAKING"; fi
if [ -n "$ADDED" ]; then SECTION="$SECTION"$'\n\n'"### Added"$'\n'"$ADDED"; fi
if [ -n "$FIXED" ]; then SECTION="$SECTION"$'\n\n'"### Fixed"$'\n'"$FIXED"; fi
if [ -n "$CHANGED" ]; then SECTION="$SECTION"$'\n\n'"### Changed"$'\n'"$CHANGED"; fi
if [ -n "$REMOVED" ]; then SECTION="$SECTION"$'\n\n'"### Removed"$'\n'"$REMOVED"; fi
if [ -z "$ADDED$FIXED$CHANGED$REMOVED" ]; then
  SECTION="$SECTION"$'\n\n'"_No documentable changes in this range._"
fi

if [ "$MODE" = "stdout" ]; then
  printf '%s\n' "$SECTION"
  printf '%s\n' "(commits reviewed: $COUNT)" >&2
  exit 0
fi

HEADER='# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).'

SECTION_FILE="$(mktemp)"
printf '%s\n' "$SECTION" > "$SECTION_FILE"

if [ ! -f "$OUT" ]; then
  printf '%s\n\n' "$HEADER" > "$OUT"
  cat "$SECTION_FILE" >> "$OUT"
elif grep -q '^## \[' "$OUT"; then
  # Insert the new section above the newest existing one, so the file stays
  # ordered from newest to oldest.
  awk 'NR==FNR { sec = sec $0 "\n"; next }
       /^## \[/ && !done { printf "%s\n", sec; done = 1 }
       { print }' "$SECTION_FILE" "$OUT" > "$OUT.tmp"
  mv "$OUT.tmp" "$OUT"
else
  printf '\n' >> "$OUT"
  cat "$SECTION_FILE" >> "$OUT"
fi
rm -f "$SECTION_FILE"

printf 'CHANGELOG updated: %s (%s commits since %s)\n' "$OUT" "$COUNT" "${SINCE:-the start of the repository}"
