#!/usr/bin/env bash
set -euo pipefail

OUTPUT="CHANGELOG.md"
REPO_ROOT=""
REVERSE=false
VERBOSE=false

show_help() {
  cat <<'HELP'
Usage: changelog.sh [OPTIONS]

Generate a structured CHANGELOG.md from git history.

Options:
  -o, --output FILE   Output file path (default: CHANGELOG.md)
  -r, --repo  DIR     Repository root directory (default: auto-detect)
  -x, --reverse       Show oldest entries first (default: newest first)
  -v, --verbose       Print commit details to stderr
  -h, --help          Show this help message

Categorization rules (conventional commits):
  Added:     feat, add, implement, introduce, create, new
  Fixed:     fix, bug, resolve, patch, correct, hotfix
  Changed:   refactor, chore, style, docs, test, ci, perf, build, update, improve, bump
  Removed:   remove, drop, delete, deprecate, revert

Examples:
  changelog.sh                     # CHANGELOG.md from last tag to HEAD
  changelog.sh -o NOTES.md         # Write to NOTES.md instead
  changelog.sh -r /path/to/repo    # Target a specific repo
  changelog.sh -x                  # Oldest first
HELP
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)  OUTPUT="$2"; shift 2 ;;
    -r|--repo)    REPO_ROOT="$2"; shift 2 ;;
    -x|--reverse) REVERSE=true; shift ;;
    -v|--verbose)  VERBOSE=true; shift ;;
    -h|--help)    show_help; exit 0 ;;
    *)            echo "Unknown option: $1" >&2; show_help; exit 1 ;;
  esac
done

cd "${REPO_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || echo .)}"

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo '')"
if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
  VERSION="${LAST_TAG#v}"
else
  RANGE="$(git rev-list --max-parents=0 HEAD)..HEAD"
  VERSION="Unreleased"
fi

TODAY="$(date +%Y-%m-%d)"
TOTAL="$(git log "$RANGE" --oneline 2>/dev/null | wc -l | tr -d ' ')"

if [ "$TOTAL" -eq 0 ]; then
  echo "No commits found in range $RANGE" >&2
  exit 1
fi

if [ "$VERBOSE" = true ]; then
  echo "Generating changelog: $RANGE ($TOTAL commits)" >&2
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
UNCATEGORIZED=""

categorize() {
  local msg="$1"
  local stripped="$msg"

  # Strip conventional commit type prefix for the bullet text
  if echo "$msg" | grep -qiE '^[a-z]+(\([^)]+\))?:'; then
    stripped="$(echo "$msg" | sed -E 's/^[a-z]+(\([^)]+\))?:\s*//')"
  fi

  if echo "$msg" | grep -qiE '^(feat|add|implement|introduce|create|new)\b'; then
    ADDED+="- ${stripped}"$'\n'
  elif echo "$msg" | grep -qiE '^(fix|bug|resolve|patch|correct|hotfix)\b'; then
    FIXED+="- ${stripped}"$'\n'
  elif echo "$msg" | grep -qiE '^(remove|drop|delete|deprecate|revert)\b'; then
    REMOVED+="- ${stripped}"$'\n'
  elif echo "$msg" | grep -qiE '^(chore|refactor|style|docs|test|ci|perf|build|update|improve|bump)\b'; then
    CHANGED+="- ${stripped}"$'\n'
  else
    UNCATEGORIZED+="- ${msg}"$'\n'
  fi
}

while IFS= read -r msg; do
  [ -z "$msg" ] && continue
  msg="$(echo "$msg" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  categorize "$msg"
done < <(git log "$RANGE" --pretty=format:"%s" 2>/dev/null)

render_section() {
  local title="$1"
  local content="$2"
  if [ -n "$content" ]; then
    echo "### $title"
    echo ""
    printf '%s' "$content"
    echo ""
  fi
}

{
  echo "# Changelog"
  echo ""
  echo "## ${VERSION} (${TODAY})"
  echo ""

  if [ "$REVERSE" = true ]; then
    render_section "Added"      "$ADDED"
    render_section "Fixed"      "$FIXED"
    render_section "Changed"    "$CHANGED"
    render_section "Removed"    "$REMOVED"
    render_section "Other"      "$UNCATEGORIZED"
  else
    render_section "Added"      "$ADDED"
    render_section "Fixed"      "$FIXED"
    render_section "Changed"    "$CHANGED"
    render_section "Removed"    "$REMOVED"
    render_section "Other"      "$UNCATEGORIZED"
  fi

  echo "---"
  echo "_${TOTAL} commits covering ${RANGE}_"
} > "$OUTPUT"

echo "Generated ${OUTPUT} (${VERSION}, ${TOTAL} commits)"