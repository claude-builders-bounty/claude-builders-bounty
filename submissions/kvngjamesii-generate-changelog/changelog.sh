#!/usr/bin/env bash
# changelog.sh — structured CHANGELOG.md from git history (Keep a Changelog).
# Usage:
#   bash changelog.sh                 # since last tag → CHANGELOG.md
#   bash changelog.sh v1.2.0          # since explicit ref
#   bash changelog.sh --stdout        # print only
#   bash changelog.sh --since v1.0.0 --stdout
set -euo pipefail

SINCE=""
OUTFILE="CHANGELOG.md"
STDOUT_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stdout|-o-) STDOUT_ONLY=1; shift ;;
    --since) SINCE="${2:-}"; shift 2 ;;
    --out) OUTFILE="${2:-CHANGELOG.md}"; shift 2 ;;
    -h|--help)
      sed -n '2,8p' "$0"
      exit 0
      ;;
    *)
      if [[ -z "$SINCE" && "$1" != --* ]]; then SINCE="$1"; shift
      else echo "Unknown arg: $1" >&2; exit 2; fi
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: not a git repository" >&2
  exit 1
fi

if [[ -z "$SINCE" ]]; then
  SINCE="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [[ -n "$SINCE" ]]; then
  RANGE="${SINCE}..HEAD"
  HEADER_RANGE="Unreleased (since ${SINCE})"
else
  RANGE="HEAD"
  HEADER_RANGE="Unreleased (full history)"
fi

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT
for g in Added Fixed Changed Removed; do : >"$TMPDIR/$g"; done

# Categorize: conventional commits first, then message-keyword heuristics.
categorize() {
  local msg="$1" lower
  lower="$(printf '%s' "$msg" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feat\(*\):*|add:*|added:*) echo Added; return ;;
    fix:*|fix\(*\):*|bugfix:*|hotfix:*) echo Fixed; return ;;
    refactor:*|refactor\(*\):*|perf:*|perf\(*\):*|style:*|chore:*|build:*|ci:*|docs:*|change:*|changed:*|update:*|updated:*) echo Changed; return ;;
    remove:*|removed:*|delete:*|deleted:*|revert:*|drop:*) echo Removed; return ;;
  esac

  case "$lower" in
    *\ remove\ *|*\ removed\ *|*\ delete\ *|*\ deleted\ *|*\ drop\ *|*\ dropping\ *) echo Removed; return ;;
    *\ fix\ *|*\ fixed\ *|*\ bug\ *|*\ hotfix\ *|*\ patch\ *) echo Fixed; return ;;
    *\ add\ *|*\ added\ *|*\ introduce\ *|*\ new\ *) echo Added; return ;;
    *\ change\ *|*\ changed\ *|*\ update\ *|*\ updated\ *|*\ rename\ *|*\ improve\ *) echo Changed; return ;;
  esac

  # Leading verb heuristics (non-conventional subjects)
  case "$lower" in
    add\ *|added\ *|introduce\ *|implement\ *) echo Added; return ;;
    fix\ *|fixed\ *|bugfix\ *|hotfix\ *) echo Fixed; return ;;
    remove\ *|removed\ *|delete\ *|deleted\ *|drop\ *|revert\ *) echo Removed; return ;;
    update\ *|updated\ *|change\ *|changed\ *|refactor\ *|improve\ *|rename\ *) echo Changed; return ;;
  esac

  echo Changed
}

count=0
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  hash="${line%%$'\t'*}"
  msg="${line#*$'\t'}"
  [[ -z "$msg" ]] && continue
  case "$msg" in
    Merge\ *|merge\ *) continue ;;
  esac
  grp="$(categorize "$msg")"
  # strip conventional type prefix for cleaner bullets
  clean="$(printf '%s' "$msg" | sed -E 's/^[A-Za-z]+(\([^)]*\))?!?:[[:space:]]*//')"
  # capitalize first letter of description
  if [[ -n "$clean" ]]; then
    first="$(printf '%s' "${clean:0:1}" | tr '[:lower:]' '[:upper:]')"
    clean="${first}${clean:1}"
  fi
  printf -- '- %s (`%s`)\n' "$clean" "$hash" >>"$TMPDIR/$grp"
  count=$((count + 1))
done < <(git log --no-merges --pretty=tformat:'%h%x09%s' "$RANGE")

DATE="$(date -u +%Y-%m-%d)"
REPO_URL="$(git remote get-url origin 2>/dev/null || true)"
REPO_URL="${REPO_URL%.git}"
REPO_URL="${REPO_URL/git@github.com:/https:\/\/github.com\/}"

{
  echo "# Changelog"
  echo
  echo "All notable changes are documented in this file."
  echo
  echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)."
  echo
  echo "## [${HEADER_RANGE}] - ${DATE}"
  if [[ -n "$REPO_URL" && -n "$SINCE" ]]; then
    echo
    echo "Compare: ${REPO_URL}/compare/${SINCE}...HEAD"
  fi
  echo
  empty=1
  for g in Added Fixed Changed Removed; do
    if [[ -s "$TMPDIR/$g" ]]; then
      empty=0
      echo "### $g"
      echo
      cat "$TMPDIR/$g"
      echo
    fi
  done
  if [[ "$empty" -eq 1 ]]; then
    echo "_No commits in range \`${RANGE}\`._"
    echo
  fi
} >"$TMPDIR/section.md"

if [[ "$STDOUT_ONLY" -eq 1 ]]; then
  cat "$TMPDIR/section.md"
else
  if [[ -f "$OUTFILE" ]] && grep -q '^# Changelog' "$OUTFILE" 2>/dev/null; then
    # Prepend new section under the title block
    {
      head -n 1 "$OUTFILE"
      echo
      # skip first heading line from section (already have # Changelog)
      tail -n +2 "$TMPDIR/section.md"
      # rest of old file without its first # Changelog line
      tail -n +2 "$OUTFILE"
    } >"$TMPDIR/merged.md"
    mv "$TMPDIR/merged.md" "$OUTFILE"
  else
    cp "$TMPDIR/section.md" "$OUTFILE"
  fi
  echo "Wrote ${OUTFILE} (${count} commits, range ${RANGE})" >&2
fi
