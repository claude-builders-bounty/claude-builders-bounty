#!/usr/bin/env bash
# changelog.sh — generate CHANGELOG.md from git history.
# Usage: bash changelog.sh [--output FILE] [--from REF] [--unreleased]
# Commits since the last git tag (or --from REF) are categorized by
# conventional-commit prefix into Added / Fixed / Changed / Removed.
set -euo pipefail

OUT="CHANGELOG.md"
FROM=""
TITLE="Unreleased"
while [ $# -gt 0 ]; do
  case "$1" in
    --output) OUT="$2"; shift 2 ;;
    --from)   FROM="$2"; shift 2 ;;
    *)        echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

# range: last tag..HEAD, or all commits if no tags
if [ -z "$FROM" ]; then
  LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
  if [ -n "$LAST_TAG" ]; then RANGE="${LAST_TAG}..HEAD"; FROM_LABEL="$LAST_TAG";
  else RANGE="HEAD"; FROM_LABEL="(no tags — full history)"; fi
else
  RANGE="${FROM}..HEAD"; FROM_LABEL="$FROM"
fi

declare -A B=( [Added]="" [Fixed]="" [Changed]="" [Removed]="" )

while IFS= read -r line; do
  subj="${line#* }"
  lower="$(printf '%s' "$subj" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    feat:*|feat\(*|add*|feature*)        k="Added" ;;
    fix:*|fix\(*|bugfix*|hotfix*)        k="Fixed" ;;
    remove*|revert*|drop*|deleted*)      k="Removed" ;;
    *)                                   k="Changed" ;;
  esac
  hash="$(printf '%s' "$line" | cut -d' ' -f1 | cut -c1-7)"
  B[$k]="${B[$k]}- ${subj} (\`${hash}\`)\n"
done < <(git log "$RANGE" --pretty=tformat:'%H %s' --no-merges 2>/dev/null)

DATE="$(date +%Y-%m-%d)"
{
  echo "# Changelog"
  echo
  echo "All notable changes to this project will be documented in this file."
  echo "Format follows [Keep a Changelog](https://keepachangelog.com/)."
  echo
  echo "## [$TITLE] — $DATE"
  echo
  echo "_Range: \`${FROM_LABEL}\`..HEAD_"
  for k in Added Fixed Changed Removed; do
    if [ -n "${B[$k]}" ]; then
      echo
      echo "### $k"
      echo
      printf '%b' "${B[$k]}"
    fi
  done
} > "$OUT"
echo "wrote $OUT (range: ${FROM_LABEL}..HEAD)"
