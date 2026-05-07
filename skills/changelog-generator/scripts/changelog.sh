#!/usr/bin/env bash
# Generate a Keep-A-Changelog formatted CHANGELOG section from git history.
#
# Usage:
#   bash changelog.sh [--since vX.Y.Z] [--until HEAD] [--out CHANGELOG.md] [--version v1.2.3]
#
# Zero-dependency apart from git, awk, and a POSIX shell.

set -euo pipefail

SINCE=""
UNTIL="HEAD"
OUT=""
VERSION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE="$2"; shift 2 ;;
    --until) UNTIL="$2"; shift 2 ;;
    --out)   OUT="$2"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,8p' "$0" | sed 's/^# \?//'
      exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$SINCE" ]]; then
  if SINCE_TRY=$(git describe --tags --abbrev=0 2>/dev/null); then
    SINCE="$SINCE_TRY"
  else
    SINCE="$(git rev-list --max-parents=0 HEAD | head -n1)"
  fi
fi

RANGE="${SINCE}..${UNTIL}"
TODAY=$(date +%Y-%m-%d)
LABEL="${VERSION:-Unreleased}"

# Collect commits as "<sha>\t<subject>"
COMMITS=$(git log --no-merges --reverse --pretty=format:'%h%x09%s' "$RANGE" || true)

# Categorize. We emit four buckets + Other.
declare -A BUCKETS
BUCKETS=( [Added]="" [Changed]="" [Fixed]="" [Removed]="" [Other]="" )

categorize() {
  local subject="$1"
  local lc; lc="$(echo "$subject" | awk '{print tolower($0)}')"
  # conventional-commit prefix
  local cc_re='^([a-zA-Z]+)(\([^)]+\))?!?:[[:space:]]*(.+)$'
  if [[ "$subject" =~ $cc_re ]]; then
    local prefix="${BASH_REMATCH[1]}"
    local clean="${BASH_REMATCH[3]}"
    case "$(echo "$prefix" | awk '{print tolower($0)}')" in
      feat|add)                          echo "Added|$clean"; return ;;
      fix|bugfix|patch)                  echo "Fixed|$clean"; return ;;
      refactor|perf|style|chore|docs|build|ci|test|deps) echo "Changed|$clean"; return ;;
      revert|remove)                     echo "Removed|$clean"; return ;;
    esac
  fi
  # keyword fallback (order matters: Removed/Fixed first to win over Changed/Added)
  case "$lc" in
    *remove*|*deleted*|*drop*) echo "Removed|$subject"; return ;;
    *fix*|*repair*|*correct*|*resolve*) echo "Fixed|$subject"; return ;;
    *add*|*introduce*|" new "*) echo "Added|$subject"; return ;;
    *update*|*change*|*improve*|*bump*|*rename*|*refactor*) echo "Changed|$subject"; return ;;
  esac
  echo "Other|$subject"
}

# Capitalize first letter of a string.
cap_first() {
  local s="$1"
  [[ -z "$s" ]] && { echo ""; return; }
  echo "$(echo "${s:0:1}" | tr '[:lower:]' '[:upper:]')${s:1}"
}

if [[ -n "$COMMITS" ]]; then
  while IFS=$'\t' read -r sha subject; do
    [[ -z "$sha" ]] && continue
    res=$(categorize "$subject")
    bucket="${res%%|*}"
    cleaned="${res#*|}"
    cleaned=$(cap_first "$cleaned")
    BUCKETS[$bucket]+="- ${cleaned} (${sha})"$'\n'
  done <<< "$COMMITS"
fi

emit() {
  echo "## [$LABEL] - $TODAY"
  echo
  for bucket in Added Changed Fixed Removed Other; do
    if [[ -n "${BUCKETS[$bucket]:-}" ]]; then
      echo "### $bucket"
      printf '%s' "${BUCKETS[$bucket]}"
      echo
    fi
  done
}

if [[ -n "$OUT" ]]; then
  HEADER='# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

'
  if [[ ! -f "$OUT" ]]; then
    printf '%s' "$HEADER" > "$OUT"
    emit >> "$OUT"
  else
    # prepend new section right before existing "## [" sections, preserving header.
    tmp=$(mktemp)
    awk -v new="$(emit)" '
      BEGIN { printed=0 }
      /^## \[/ && !printed { print new; printed=1 }
      { print }
      END { if (!printed) print new }
    ' "$OUT" > "$tmp" && mv "$tmp" "$OUT"
  fi
  echo "wrote $OUT" >&2
else
  emit
fi
