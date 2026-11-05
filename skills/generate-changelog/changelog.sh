#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history.
# Usage: bash changelog.sh [OUTPUT_FILE]   (default: CHANGELOG.md)
set -euo pipefail

OUT="${1:-CHANGELOG.md}"
DATE="$(date +%Y-%m-%d)"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "error: not inside a git repository" >&2; exit 1
fi

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$LAST_TAG" ]; then RANGE="${LAST_TAG}..HEAD"; else RANGE="HEAD"; fi
VERSION="${LAST_TAG:-unreleased}"

add_fields=""; fix_fields=""; chg_fields=""; rem_fields=""

while IFS=$'\t' read -r sha subject; do
  [ -z "$sha" ] && continue
  low="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  case "$low" in
    feat*|feature*|add*)        bucket=Added ;;
    fix*|bug*|patch*|hotfix*)   bucket=Fixed ;;
    remov*|delete*|drop*|rm*)   bucket=Removed ;;
    *)                          bucket=Changed ;;
  esac
  if [ "$bucket" = "Changed" ]; then
    case "$low" in
      *add*|*introduce*|*implement*) bucket=Added ;;
      *fix*|*bug*|*resolve*|*repair*) bucket=Fixed ;;
      *remov*|*delete*|*drop*)        bucket=Removed ;;
    esac
  fi
  line="* ${subject} (${sha})"
  case "$bucket" in
    Added)   add_fields="${add_fields}${line}"$'\n' ;;
    Fixed)   fix_fields="${fix_fields}${line}"$'\n' ;;
    Removed) rem_fields="${rem_fields}${line}"$'\n' ;;
    *)       chg_fields="${chg_fields}${line}"$'\n' ;;
  esac
done < <(git log $RANGE --pretty=format:'%h%x09%s')

{
  echo "# Changelog"
  echo
  echo "## [${VERSION}] - ${DATE}"
  echo
  for sec in Added Fixed Changed Removed; do
    case "$sec" in
      Added)   body="$add_fields" ;;
      Fixed)   body="$fix_fields" ;;
      Changed) body="$chg_fields" ;;
      Removed) body="$rem_fields" ;;
    esac
    [ -z "$body" ] && continue
    echo "### ${sec}"
    printf '%b\n' "$body"
    echo
  done
  if [ -z "${add_fields}${fix_fields}${chg_fields}${rem_fields}" ]; then
    echo "_No commits found since ${VERSION}._"
    echo
  fi
} > "$OUT"

echo "Wrote $OUT (range: ${RANGE})"
