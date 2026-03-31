#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage:
#   bash changelog.sh                    # write/update CHANGELOG.md
#   bash changelog.sh --dry-run          # print to stdout only
#   bash changelog.sh --since v1.2.0     # override baseline tag
#   bash changelog.sh --version v2.0.0   # override output version label
#   bash changelog.sh --help
#
# Categories (conventional commits + smart fallback):
#   Added    → feat, add, new, introduce
#   Fixed    → fix, bug, patch, correct, resolve
#   Changed  → refactor, perf, update, change, improve, chore, ci, style
#   Removed  → remove, delete, drop, deprecate, revert
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Helpers ──────────────────────────────────────────────────────────────────
usage() {
  grep '^#' "$0" | grep -v '#!/' | sed 's/^# \{0,1\}//'
  exit 0
}

die() { echo "❌ $*" >&2; exit 1; }

# ── Arg parsing ──────────────────────────────────────────────────────────────
DRY_RUN=false
SINCE_TAG=""
VERSION_LABEL=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)   DRY_RUN=true; shift ;;
    --since)     SINCE_TAG="$2"; shift 2 ;;
    --version)   VERSION_LABEL="$2"; shift 2 ;;
    --help|-h)   usage ;;
    *) die "Unknown option: $1" ;;
  esac
done

# ── Sanity checks ────────────────────────────────────────────────────────────
command -v git &>/dev/null || die "git not found"
git rev-parse --git-dir &>/dev/null || die "Not inside a git repository"

# ── Resolve baseline ─────────────────────────────────────────────────────────
if [[ -n "$SINCE_TAG" ]]; then
  git rev-parse "$SINCE_TAG" &>/dev/null || die "Tag '$SINCE_TAG' not found"
  BASELINE="$SINCE_TAG"
  BASELINE_REF="${SINCE_TAG}..HEAD"
else
  BASELINE=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
  if [[ -n "$BASELINE" ]]; then
    BASELINE_REF="${BASELINE}..HEAD"
  else
    BASELINE="(initial commit)"
    BASELINE_REF="HEAD"
  fi
fi

# ── Auto-detect next version ─────────────────────────────────────────────────
if [[ -z "$VERSION_LABEL" ]]; then
  # Try package.json → Cargo.toml → pyproject.toml → fallback
  if [[ -f package.json ]]; then
    VERSION_LABEL=$(node -p "require('./package.json').version" 2>/dev/null || echo "")
    [[ -n "$VERSION_LABEL" ]] && VERSION_LABEL="v${VERSION_LABEL}"
  fi
  if [[ -z "$VERSION_LABEL" ]] && [[ -f Cargo.toml ]]; then
    VERSION_LABEL=$(grep '^version' Cargo.toml | head -1 | sed 's/.*= *"\(.*\)"/v\1/' 2>/dev/null || echo "")
  fi
  if [[ -z "$VERSION_LABEL" ]] && [[ -f pyproject.toml ]]; then
    VERSION_LABEL=$(grep '^version' pyproject.toml | head -1 | sed 's/.*= *"\(.*\)"/v\1/' 2>/dev/null || echo "")
  fi
  [[ -z "$VERSION_LABEL" ]] && VERSION_LABEL="Unreleased"
fi

DATE=$(date +%Y-%m-%d)

# ── Fetch commits ─────────────────────────────────────────────────────────────
COMMITS=$(git log "$BASELINE_REF" --no-merges --pretty=format:"%h	%s" 2>/dev/null || echo "")

if [[ -z "$COMMITS" ]]; then
  echo "ℹ️  No commits found since ${BASELINE}. Nothing to generate." >&2
  exit 0
fi

# ── Categorize ───────────────────────────────────────────────────────────────
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

while IFS='	' read -r hash subject; do
  [[ -z "$subject" ]] && continue

  # Strip conventional-commit prefix for display: "feat(scope): msg" → "msg"
  display=$(echo "$subject" | sed 's/^[a-z]*([^)]*): //' | sed 's/^[a-z]*!*: //')
  entry="- ${display} (\`${hash}\`)"

  # Classify by conventional-commit type or keyword fallback
  type=$(echo "$subject" | grep -oE '^[a-z]+' | head -1 | grep -E '^[a-z]+$' || echo "")
  subject_lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

  case "$type" in
    feat|add)  ADDED+=("$entry") ;;
    fix|bug)   FIXED+=("$entry") ;;
    refactor|perf|chore|ci|style|build|docs|test) CHANGED+=("$entry") ;;
    revert|remove|delete|drop) REMOVED+=("$entry") ;;
    *)
      # Keyword fallback
      if echo "$subject_lower" | grep -qE '(^|[^a-z])(add|new|creat|introduc|implement|feat)([^a-z]|$)'; then
        ADDED+=("$entry")
      elif echo "$subject_lower" | grep -qE '(^|[^a-z])(fix|bug|patch|correct|resolv|repair)([^a-z]|$)'; then
        FIXED+=("$entry")
      elif echo "$subject_lower" | grep -qE '(^|[^a-z])(remov|delet|drop|deprecat|revert)([^a-z]|$)'; then
        REMOVED+=("$entry")
      else
        CHANGED+=("$entry")
      fi
      ;;
  esac
done <<< "$COMMITS"

# ── Build section ─────────────────────────────────────────────────────────────
# Renders a category section to stdout if array is non-empty
# Usage: render_section "### Title" "${items[@]}"
render_section() {
  local title=$1; shift
  local items=("$@")
  if [[ ${#items[@]} -gt 0 ]]; then
    printf "\n%s\n\n" "$title"
    for item in "${items[@]}"; do echo "$item"; done
  fi
}

HEADER="## [${VERSION_LABEL}] — ${DATE}"
BODY=""
BODY+=$(render_section "### Added"   "${ADDED[@]+"${ADDED[@]}"}")
BODY+=$(render_section "### Fixed"   "${FIXED[@]+"${FIXED[@]}"}")
BODY+=$(render_section "### Changed" "${CHANGED[@]+"${CHANGED[@]}"}")
BODY+=$(render_section "### Removed" "${REMOVED[@]+"${REMOVED[@]}"}")

NEW_SECTION="${HEADER}${BODY}"

# ── Output ────────────────────────────────────────────────────────────────────
if $DRY_RUN; then
  echo "$NEW_SECTION"
  exit 0
fi

CHANGELOG_FILE="CHANGELOG.md"

if [[ -f "$CHANGELOG_FILE" ]]; then
  # Prepend new section after the first heading (or at top if no heading)
  if grep -q '^# ' "$CHANGELOG_FILE"; then
    # Insert after the first h1
    FIRST_H1_LINE=$(grep -n '^# ' "$CHANGELOG_FILE" | head -1 | cut -d: -f1)
    head -n "$FIRST_H1_LINE" "$CHANGELOG_FILE" > /tmp/cl_top.tmp
    tail -n +"$((FIRST_H1_LINE + 1))" "$CHANGELOG_FILE" > /tmp/cl_rest.tmp
    { cat /tmp/cl_top.tmp; echo ""; echo "$NEW_SECTION"; cat /tmp/cl_rest.tmp; } > "$CHANGELOG_FILE"
    rm -f /tmp/cl_top.tmp /tmp/cl_rest.tmp
  else
    { echo "$NEW_SECTION"; echo ""; cat "$CHANGELOG_FILE"; } > /tmp/cl_merged.tmp
    mv /tmp/cl_merged.tmp "$CHANGELOG_FILE"
  fi
else
  {
    echo "# Changelog"
    echo ""
    echo "All notable changes are documented here."
    echo "Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)"
    echo ""
    echo "$NEW_SECTION"
  } > "$CHANGELOG_FILE"
fi

TOTAL=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} ))
echo "✅ CHANGELOG.md updated — ${TOTAL} commits categorized (since ${BASELINE})"
echo "   Added: ${#ADDED[@]}  Fixed: ${#FIXED[@]}  Changed: ${#CHANGED[@]}  Removed: ${#REMOVED[@]}"
