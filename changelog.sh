#!/usr/bin/env bash
# changelog.sh - generate a structured CHANGELOG.md from git history.
# Usage: bash changelog.sh [output_file]   (default: CHANGELOG.md)
set -euo pipefail

OUT="${1:-CHANGELOG.md}"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "error: not inside a git repository" >&2
  exit 1
fi

cd "$(git rev-parse --show-toplevel)"

# Work out the commit range: since the last tag, or all history if no tags exist.
if tag=$(git describe --tags --abbrev=0 2>/dev/null); then
  range="${tag}..HEAD"
  version_label="${tag}+unreleased"
else
  first=$(git rev-list --max-parents=0 HEAD | tail -n 1)
  range="${first}..HEAD"
  version_label="0.0.0-unreleased"
fi

commits=$(git log "$range" --pretty=format:'%h%x09%s' --no-merges || true)

if [ -z "$commits" ]; then
  echo "No commits after ${range%%..*}; nothing to add."
  exit 0
fi

added=""; fixed=""; changed=""; removed=""

while IFS=$'\t' read -r hash subject; do
  [ -z "${subject:-}" ] && continue
  lower=$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')
  case "$lower" in
    feat*|*"add feature"*|*"add support"*|*" add "*|*"added "*) bucket="added" ;;
    *"remove"*|*"delete"*|*"drop "*|*"deprecat"*) bucket="removed" ;;
    fix*|*"bug"*|*"patch"*|*"hotfix"*) bucket="fixed" ;;
    refactor*|*"change"*|*"update"*|perf*|docs*|chore*|style*|test*|build*|ci*) bucket="changed" ;;
    *) bucket="changed" ;;
  esac
  clean=$(printf '%s' "$subject" | sed -E 's/^[A-Za-z]+(\([^)]*\))?!?:[[:space:]]*//')
  bullet="- ${clean} (\`${hash}\`)"
  case "$bucket" in
    added) added="${added}${bullet}"$'\n' ;;
    fixed) fixed="${fixed}${bullet}"$'\n' ;;
    removed) removed="${removed}${bullet}"$'\n' ;;
    *) changed="${changed}${bullet}"$'\n' ;;
  esac
done <<< "$commits"

{
  echo "# Changelog"
  echo
  echo "## ${version_label} - $(date -u +%Y-%m-%d)"
  echo
  for section in added fixed changed removed; do
    case "$section" in
      added) label="Added"; body="$added" ;;
      fixed) label="Fixed"; body="$fixed" ;;
      changed) label="Changed"; body="$changed" ;;
      removed) label="Removed"; body="$removed" ;;
    esac
    if [ -n "$body" ]; then
      echo "### ${label}"
      echo
      printf '%s' "$body"
      echo
    fi
  done
} > "$OUT"

echo "Wrote ${OUT}: $(grep -c '^- ' "$OUT" || true) entries"
