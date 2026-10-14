#!/usr/bin/env bash
# changelog.sh - generate a structured CHANGELOG.md from git history.
# Usage: bash changelog.sh [-o FILE] [-r REPO_DIR] [-v VERSION]
# Commits since the last git tag (or all commits if no tag) are grouped
# into Added / Fixed / Changed / Removed.
set -euo pipefail

OUT="CHANGELOG.md"; REPO="."; VERSION=""
while getopts "o:r:v:h" opt; do
  case "$opt" in
    o) OUT="$OPTARG" ;;
    r) REPO="$OPTARG" ;;
    v) VERSION="$OPTARG" ;;
    *) sed -n '2,5p' "$0"; exit 0 ;;
  esac
done

command -v git >/dev/null || { echo "git is required" >&2; exit 1; }
git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1 \
  || { echo "Not a git repository: $REPO" >&2; exit 1; }
git -C "$REPO" rev-parse HEAD >/dev/null 2>&1 \
  || { echo "Repository has no commits" >&2; exit 1; }

LAST_TAG="$(git -C "$REPO" describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$LAST_TAG" ]; then RANGE="${LAST_TAG}..HEAD"; else RANGE="HEAD"; fi
[ -n "$VERSION" ] || VERSION="Unreleased"

ADDED=""; FIXED=""; CHANGED=""; REMOVED=""
nl=$'\n'
while IFS=$'\x1f' read -r hash subject; do
  [ -n "$hash" ] || continue
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  msg="$(printf '%s' "$subject" | sed -E 's/^[A-Za-z]+(\([^)]*\))?!?:[[:space:]]*//')"
  [ -n "$msg" ] || msg="$subject"
  line="- ${msg} (${hash})${nl}"
  case "$lower" in
    feat*|add*|new*|implement*|create*|introduce*) ADDED+="$line" ;;
    fix*|bug*|hotfix*|resolve*|patch*)             FIXED+="$line" ;;
    remove*|delete*|drop*|deprecate*|revert*)      REMOVED+="$line" ;;
    *)                                             CHANGED+="$line" ;;
  esac
done < <(git -C "$REPO" log --no-merges --pretty=format:'%h%x1f%s' "$RANGE")

{
  echo "# Changelog"
  echo
  echo "## [${VERSION}] - $(date +%Y-%m-%d)"
  if [ -n "$LAST_TAG" ]; then echo "_Changes since ${LAST_TAG}_"; fi
  for sec in Added Fixed Changed Removed; do
    case "$sec" in
      Added) body="$ADDED" ;; Fixed) body="$FIXED" ;;
      Changed) body="$CHANGED" ;; Removed) body="$REMOVED" ;;
    esac
    [ -n "$body" ] || continue
    echo; echo "### $sec"; printf '%s' "$body"
  done
} > "$OUT"
echo "Wrote $OUT (range: $RANGE)"
