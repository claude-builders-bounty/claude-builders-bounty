#!/usr/bin/env bash
#
# changelog.sh — generate a structured CHANGELOG.md from git history.
#
# Collects commits since the most recent git tag (or the whole history if the
# repo has no tags), buckets them into Added / Changed / Fixed / Removed by
# reading Conventional-Commit types and keywords, and writes a Keep-a-Changelog
# formatted CHANGELOG.md.
#
# Usage:
#   bash changelog.sh                 # write ./CHANGELOG.md
#   bash changelog.sh -o CHANGES.md   # custom output file
#   bash changelog.sh --stdout        # print to stdout, write nothing
#   bash changelog.sh --since v1.2.0  # force the starting ref
#
set -euo pipefail

OUT="CHANGELOG.md"
SINCE=""
TO_STDOUT=0

while [ $# -gt 0 ]; do
  case "$1" in
    -o|--output) OUT="$2"; shift 2 ;;
    --since)     SINCE="$2"; shift 2 ;;
    --stdout)    TO_STDOUT=1; shift ;;
    -h|--help)   sed -n '3,20p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

git rev-parse --git-dir >/dev/null 2>&1 || { echo "error: not a git repository" >&2; exit 1; }

# Determine the starting point: explicit --since, else the latest tag, else the
# repo's first commit (so a tag-less repo still produces a full changelog).
if [ -z "$SINCE" ]; then
  SINCE="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi
if [ -n "$SINCE" ]; then
  RANGE="${SINCE}..HEAD"
  HEADING_NOTE="since \`${SINCE}\`"
else
  RANGE="HEAD"
  HEADING_NOTE="full history (no tags found)"
fi

DATE="$(date +%Y-%m-%d)"

# Buckets (kept as newline-delimited strings for portability across bash 3.2).
ADDED=""; CHANGED=""; FIXED=""; REMOVED=""

# Read commits as "subject<TAB>shorthash", skipping merge commits.
while IFS=$'\t' read -r subject hash; do
  [ -z "$subject" ] && continue

  # skip release/version-bump commits (e.g. "3.0.0", "v1.2.0", "Release 2.1")
  printf '%s' "$subject" | grep -qiE '^(v|release[[:space:]]+v?)?[0-9]+\.[0-9]+(\.[0-9]+)?$' && continue

  # strip a Conventional-Commit "type(scope): " or "type: " prefix, capture type
  type="$(printf '%s' "$subject" | sed -nE 's/^([a-zA-Z]+)(\([^)]*\))?!?:.*/\1/p' | tr '[:upper:]' '[:lower:]')"
  clean="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?!?:[[:space:]]*//')"
  lc="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  line="- ${clean} (${hash})"

  case "$type" in
    feat|feature)              ADDED+="${line}"$'\n'; continue ;;
    fix|bugfix|hotfix)         FIXED+="${line}"$'\n'; continue ;;
    revert|remove|deprecate)   REMOVED+="${line}"$'\n'; continue ;;
    perf|refactor|change|style|build|deps) CHANGED+="${line}"$'\n'; continue ;;
    chore|docs|test|ci)        continue ;;  # housekeeping — omit from changelog
  esac

  # No conventional type — fall back to keyword sniffing.
  case "$lc" in
    add*|"new "*|introduc*|implement*|support*) ADDED+="${line}"$'\n' ;;
    fix*|bug*|patch*|resolv*|correct*)          FIXED+="${line}"$'\n' ;;
    remov*|delet*|drop*|revert*)                REMOVED+="${line}"$'\n' ;;
    merge\ *)                                    : ;;  # stray merge subject
    *)                                           CHANGED+="${line}"$'\n' ;;
  esac
# tformat (not format) terminates EVERY record with a newline, incl. the last —
# otherwise `read` drops the oldest commit, which has no trailing newline.
done < <(git log "$RANGE" --no-merges --pretty=tformat:'%s%x09%h')

emit_section() { # title, body
  [ -z "$2" ] && return 0
  printf '### %s\n%s\n' "$1" "$2"
}

render() {
  printf '# Changelog\n\n'
  printf 'All notable changes to this project, %s.\n' "$HEADING_NOTE"
  printf 'Format based on [Keep a Changelog](https://keepachangelog.com/).\n\n'
  printf '## [Unreleased] - %s\n\n' "$DATE"
  if [ -z "${ADDED}${CHANGED}${FIXED}${REMOVED}" ]; then
    printf '_No changes recorded for this range._\n'
    return
  fi
  emit_section "Added"   "$ADDED"
  emit_section "Changed" "$CHANGED"
  emit_section "Fixed"   "$FIXED"
  emit_section "Removed" "$REMOVED"
}

if [ "$TO_STDOUT" -eq 1 ]; then
  render
else
  render > "$OUT"
  echo "Wrote $OUT ($HEADING_NOTE)."
fi
