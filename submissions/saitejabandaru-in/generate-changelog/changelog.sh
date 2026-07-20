#!/usr/bin/env bash
# =============================================================================
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage:  bash changelog.sh [OPTIONS]
#   -o, --output FILE    Output file (default: CHANGELOG.md)
#   -t, --tag TAG        Start from this tag (default: last tag)
#   -r, --repo URL       Repository URL for commit links
#   -h, --help           Show this help message
# =============================================================================
set -euo pipefail

# ── Defaults ─────────────────────────────────────────────────────────────────
OUTPUT="CHANGELOG.md"
CUSTOM_TAG=""
REPO_URL=""

# ── Argument parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)  OUTPUT="$2"; shift 2 ;;
    -t|--tag)     CUSTOM_TAG="$2"; shift 2 ;;
    -r|--repo)    REPO_URL="$2"; shift 2 ;;
    -h|--help)    sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ── Ensure we're in a git repo ────────────────────────────────────────────────
if ! git rev-parse --git-dir &>/dev/null; then
  echo "❌  Not a git repository. Run from your project root." >&2
  exit 1
fi

# ── Detect repo URL ───────────────────────────────────────────────────────────
if [[ -z "$REPO_URL" ]]; then
  RAW_URL=$(git remote get-url origin 2>/dev/null || true)
  if [[ -n "$RAW_URL" ]]; then
    REPO_URL=$(echo "$RAW_URL" \
      | sed 's|git@github.com:|https://github.com/|' \
      | sed 's|\.git$||')
  fi
fi

# ── Determine tag baseline ────────────────────────────────────────────────────
if [[ -n "$CUSTOM_TAG" ]]; then
  LAST_TAG="$CUSTOM_TAG"
elif LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
  :
else
  LAST_TAG=""
fi

if [[ -n "$LAST_TAG" ]]; then
  LOG_RANGE="${LAST_TAG}..HEAD"
  TAG_LABEL="\`${LAST_TAG}\`"
else
  LOG_RANGE="HEAD"
  TAG_LABEL="the beginning"
fi

TODAY=$(date +%Y-%m-%d)

# ── Category accumulators (newline-delimited strings) ─────────────────────────
ADDED="" FIXED="" CHANGED="" REMOVED="" OTHER=""
TOTAL=0

# ── Categorize a single commit ────────────────────────────────────────────────
categorize() {
  local hash="$1" author="$2" subject="$3"
  local short_hash="${hash:0:7}"

  # Build commit link
  if [[ -n "$REPO_URL" ]]; then
    local link="[\`${short_hash}\`](${REPO_URL}/commit/${hash})"
  else
    local link="\`${short_hash}\`"
  fi

  # Strip conventional commit prefix from display message
  local msg
  msg=$(echo "$subject" \
    | sed -E 's/^(feat|fix|docs|style|refactor|perf|test|chore|revert|build|ci|remove|drop|add|new|feature|bugfix|hotfix|patch|update|change|improve|delete|deprecate)(\([^)]*\))?!?:[[:space:]]*//')

  local entry="- ${msg} (${link}) — _${author}_"

  if echo "$subject" | grep -qiE '^(feat|add|new|feature)(\([^)]*\))?!?:'; then
    ADDED="${ADDED}${entry}"$'\n'
  elif echo "$subject" | grep -qiE '^(fix|bug|bugfix|hotfix|patch)(\([^)]*\))?!?:'; then
    FIXED="${FIXED}${entry}"$'\n'
  elif echo "$subject" | grep -qiE '^(refactor|chore|style|perf|docs|improve|update|change|ci|build|test)(\([^)]*\))?!?:'; then
    CHANGED="${CHANGED}${entry}"$'\n'
  elif echo "$subject" | grep -qiE '^(remove|delete|drop|deprecate|revert)(\([^)]*\))?!?:'; then
    REMOVED="${REMOVED}${entry}"$'\n'
  else
    OTHER="${OTHER}${entry}"$'\n'
  fi
}

# ── Process commits ───────────────────────────────────────────────────────────
while IFS='|' read -r hash author subject; do
  [[ -z "$hash" ]] && continue
  categorize "$hash" "$author" "$subject"
  TOTAL=$((TOTAL + 1))
done < <(git log "$LOG_RANGE" \
  --pretty=format:"%H|%an|%s" \
  --no-merges 2>/dev/null || true)

# ── Count per category ────────────────────────────────────────────────────────
count_lines() { [[ -z "$1" ]] && echo 0 || echo "$1" | grep -c '^-' || true; }
N_ADDED=$(count_lines "$ADDED")
N_FIXED=$(count_lines "$FIXED")
N_CHANGED=$(count_lines "$CHANGED")
N_REMOVED=$(count_lines "$REMOVED")
N_OTHER=$(count_lines "$OTHER")

# ── Write CHANGELOG.md ────────────────────────────────────────────────────────
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""

  if [[ -n "$LAST_TAG" ]]; then
    echo "## [Unreleased] — ${TODAY}"
    echo ""
    plural=$( [ "$TOTAL" -ne 1 ] && echo "commits" || echo "commit" )
    echo "> Changes since ${TAG_LABEL} (${TOTAL} ${plural})"
  else
    echo "## [Initial Release] — ${TODAY}"
    echo ""
    plural=$( [ "$TOTAL" -ne 1 ] && echo "commits" || echo "commit" )
    echo "> Full history (${TOTAL} ${plural})"
  fi
  echo ""

  if [[ -n "$ADDED" ]]; then
    echo "### ✨ Added"
    printf '%s' "$ADDED"
    echo ""
  fi

  if [[ -n "$FIXED" ]]; then
    echo "### 🐛 Fixed"
    printf '%s' "$FIXED"
    echo ""
  fi

  if [[ -n "$CHANGED" ]]; then
    echo "### 🔄 Changed"
    printf '%s' "$CHANGED"
    echo ""
  fi

  if [[ -n "$REMOVED" ]]; then
    echo "### 🗑️ Removed"
    printf '%s' "$REMOVED"
    echo ""
  fi

  if [[ -n "$OTHER" ]]; then
    echo "### 📝 Other"
    printf '%s' "$OTHER"
    echo ""
  fi

  if [[ "$TOTAL" -eq 0 ]]; then
    echo "> ℹ️ No commits found since ${TAG_LABEL}."
    echo ""
  fi

} > "$OUTPUT"

# ── Summary ───────────────────────────────────────────────────────────────────
echo "✅  CHANGELOG written to: ${OUTPUT}"
echo "    Range  : ${LOG_RANGE}"
echo "    Commits: ${TOTAL}"
echo "    ✨ Added   : ${N_ADDED}"
echo "    🐛 Fixed   : ${N_FIXED}"
echo "    🔄 Changed : ${N_CHANGED}"
echo "    🗑️  Removed : ${N_REMOVED}"
echo "    📝 Other   : ${N_OTHER}"
