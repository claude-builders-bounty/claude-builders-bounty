#!/usr/bin/env bash
# changelog.sh — generate a Keep-a-Changelog style CHANGELOG.md from git history
# since the last git tag.
#
# Categorizes commits into Added / Fixed / Changed / Removed using:
#   1. Conventional Commits prefix (feat:, fix:, chore:, etc.)
#   2. Keyword heuristics on the subject line (add/fix/update/remove/...)
#
# Usage:
#   bash changelog.sh > CHANGELOG.md
#   bash changelog.sh --since v1.2.0 > CHANGELOG.md
#   bash changelog.sh --next-version v2.0.0 > CHANGELOG.md
set -euo pipefail

NEXT_VERSION=""
SINCE_TAG=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --since)        SINCE_TAG="$2"; shift 2 ;;
    --next-version) NEXT_VERSION="$2"; shift 2 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: not inside a git repository." >&2
  exit 1
fi

if [ -z "$SINCE_TAG" ]; then
  SINCE_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [ -n "$SINCE_TAG" ]; then
  RANGE="${SINCE_TAG}..HEAD"
  RANGE_LABEL="since ${SINCE_TAG}"
else
  RANGE=""
  RANGE_LABEL="all commits (no prior tag found)"
fi

if [ -z "$NEXT_VERSION" ]; then
  if [ -n "$SINCE_TAG" ]; then
    # Bump patch version of last tag (v1.2.3 -> v1.2.4)
    NEXT_VERSION="$(printf '%s' "$SINCE_TAG" | awk -F. 'BEGIN{OFS="."} {$NF=$NF+1; print}')"
    [ -z "$NEXT_VERSION" ] && NEXT_VERSION="Unreleased"
  else
    NEXT_VERSION="Unreleased"
  fi
fi

TODAY="$(date -u +%Y-%m-%d)"

# Collect commits as: hash|subject
COMMITS_FILE="$(mktemp)"
trap 'rm -f "$COMMITS_FILE"' EXIT

if [ -n "$RANGE" ]; then
  git log "$RANGE" --no-merges --pretty=format:'%h|%s' > "$COMMITS_FILE"
else
  git log --no-merges --pretty=format:'%h|%s' > "$COMMITS_FILE"
fi

# Use POSIX sed regex; classification result -> tmp files per category
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$COMMITS_FILE" "$TMP_DIR"' EXIT
: > "$TMP_DIR/added"
: > "$TMP_DIR/fixed"
: > "$TMP_DIR/changed"
: > "$TMP_DIR/removed"
: > "$TMP_DIR/other"

classify() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  # Conventional Commits prefix
  case "$lower" in
    feat:*|feat\(*\):*)                       echo added ;;
    fix:*|fix\(*\):*|hotfix:*|bugfix:*)       echo fixed ;;
    chore:*|chore\(*\):*|refactor:*|refactor\(*\):*|perf:*|perf\(*\):*|style:*|style\(*\):*|docs:*|docs\(*\):*|doc:*|doc\(*\):*|test:*|test\(*\):*|ci:*|ci\(*\):*|build:*|build\(*\):*) echo changed ;;
    remove:*|remove\(*\):*|drop:*|drop\(*\):*|deprecate:*|deprecate\(*\):*) echo removed ;;
    revert:*|revert\(*\):*)                   echo changed ;;
    *)
      # Keyword fallback
      case " $lower " in
        *" remove "*|*" delete "*|*" deprecate "*|*" drop "*) echo removed ;;
        *" fix "*|*" fixes "*|*" fixed "*|*" bug "*|*" patch "*|*" resolve "*|*" hotfix "*) echo fixed ;;
        *" add "*|*" adds "*|*" added "*|*" new "*|*" implement "*|*" support "*|*" introduce "*) echo added ;;
        *" update "*|*" change "*|*" modify "*|*" refactor "*|*" improve "*|*" tweak "*|*" rename "*|*" cleanup "*|*" bump "*) echo changed ;;
        *) echo other ;;
      esac
      ;;
  esac
}

while IFS='|' read -r hash subject; do
  [ -z "$hash" ] && continue
  cat=$(classify "$subject")
  printf -- '- %s (`%s`)\n' "$subject" "$hash" >> "$TMP_DIR/$cat"
done < "$COMMITS_FILE"

# Emit Markdown
cat <<HEADER
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [${NEXT_VERSION}] - ${TODAY}

_${RANGE_LABEL}_
HEADER

emit_section() {
  local title="$1"
  local file="$2"
  if [ -s "$file" ]; then
    echo
    echo "### ${title}"
    echo
    cat "$file"
  fi
}

emit_section "Added"   "$TMP_DIR/added"
emit_section "Fixed"   "$TMP_DIR/fixed"
emit_section "Changed" "$TMP_DIR/changed"
emit_section "Removed" "$TMP_DIR/removed"
emit_section "Other"   "$TMP_DIR/other"
