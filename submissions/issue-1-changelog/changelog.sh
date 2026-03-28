#!/usr/bin/env bash
# Works with bash 3.2+ (macOS default) and bash 4/5+
# changelog.sh — generate a structured CHANGELOG.md from git history
#
# Usage:
#   bash changelog.sh                  # auto-detects last tag, writes CHANGELOG.md
#   bash changelog.sh --since v1.2.3   # start from a specific tag
#   bash changelog.sh --output HISTORY.md
#   bash changelog.sh --dry-run        # print to stdout, don't write file
#   bash changelog.sh --help
#
# Requires: git (any version >= 2.0)

set -euo pipefail

# ── defaults ──────────────────────────────────────────────────────────────────
OUTPUT="CHANGELOG.md"
DRY_RUN=false
SINCE_TAG=""
REPO_URL=""

# ── parse args ────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since)    SINCE_TAG="$2"; shift 2 ;;
    --output)   OUTPUT="$2";    shift 2 ;;
    --dry-run)  DRY_RUN=true;   shift   ;;
    --help|-h)
      sed -n '3,15p' "$0"
      exit 0
      ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
done

# ── helpers ───────────────────────────────────────────────────────────────────
die() { echo "ERROR: $*" >&2; exit 1; }

is_inside_git_repo() {
  git rev-parse --is-inside-work-tree &>/dev/null
}

get_last_tag() {
  # Most recent tag reachable from HEAD
  git describe --tags --abbrev=0 HEAD 2>/dev/null || echo ""
}

get_repo_url() {
  git remote get-url origin 2>/dev/null | \
    sed 's|git@github.com:|https://github.com/|; s|\.git$||' || echo ""
}

# Categorize a commit subject line into Added/Fixed/Changed/Removed
categorize() {
  local msg="$1"
  local lower
  lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  # Conventional commits: feat/fix/docs/refactor/chore/test/build/ci/perf/revert
  if [[ "$lower" =~ ^(feat|add|implement|create|introduce|new) ]]; then
    echo "Added"
  elif [[ "$lower" =~ ^(fix|bug|patch|resolve|correct|hotfix) ]]; then
    echo "Fixed"
  elif [[ "$lower" =~ ^(remove|delete|drop|deprecat) ]]; then
    echo "Removed"
  elif [[ "$lower" =~ ^(refactor|revert|perf|optim|improve|update|upgrade|bump|change|migrate|rename) ]]; then
    echo "Changed"
  elif [[ "$lower" =~ ^(docs?|readme|comment|changelog|license) ]]; then
    echo "Changed"
  elif [[ "$lower" =~ ^(test|spec|ci|build|chore) ]]; then
    echo "Changed"
  else
    echo "Changed"
  fi
}

# ── main ──────────────────────────────────────────────────────────────────────
is_inside_git_repo || die "Not inside a git repository."

REPO_URL=$(get_repo_url)

if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(get_last_tag)
fi

if [[ -n "$SINCE_TAG" ]]; then
  RANGE="${SINCE_TAG}..HEAD"
  SINCE_LABEL="since \`${SINCE_TAG}\`"
else
  RANGE="HEAD"
  SINCE_LABEL="all commits"
  echo "Warning: no tags found — including all commits." >&2
fi

# Collect commits: hash|subject (bash 3.2-compatible — no mapfile)
COMMITS=()
while IFS= read -r line; do
  [[ -n "$line" ]] && COMMITS+=("$line")
done < <(
  git log "$RANGE" --no-merges \
    --format="%H|%s" \
    --reverse 2>/dev/null || true
)

if [[ ${#COMMITS[@]} -eq 0 ]]; then
  echo "No commits found ${SINCE_LABEL}. Nothing to generate." >&2
  exit 0
fi

# Build category buckets
# bash 3.2 doesn't have associative arrays — use plain vars
BUCKET_Added=""
BUCKET_Fixed=""
BUCKET_Changed=""
BUCKET_Removed=""

for entry in "${COMMITS[@]}"; do
  HASH="${entry%%|*}"
  SUBJECT="${entry#*|}"
  SHORT="${HASH:0:7}"
  CAT=$(categorize "$SUBJECT")

  if [[ -n "$REPO_URL" ]]; then
    LINE="- ${SUBJECT} ([${SHORT}](${REPO_URL}/commit/${HASH}))"
  else
    LINE="- ${SUBJECT} (\`${SHORT}\`)"
  fi

  # Append to the correct bucket variable
  case "$CAT" in
    Added)   BUCKET_Added="${BUCKET_Added}${LINE}"$'\n' ;;
    Fixed)   BUCKET_Fixed="${BUCKET_Fixed}${LINE}"$'\n' ;;
    Changed) BUCKET_Changed="${BUCKET_Changed}${LINE}"$'\n' ;;
    Removed) BUCKET_Removed="${BUCKET_Removed}${LINE}"$'\n' ;;
  esac
done

# Determine version header
TODAY=$(date +%Y-%m-%d)
NEXT_TAG=""
# Try to infer next version from latest tag
if [[ -n "$SINCE_TAG" ]]; then
  # Strip leading 'v'
  BASE="${SINCE_TAG#v}"
  IFS='.' read -r -a PARTS <<< "$BASE"
  if [[ ${#PARTS[@]} -ge 3 ]]; then
    PATCH=$(( PARTS[2] + 1 ))
    NEXT_TAG="v${PARTS[0]}.${PARTS[1]}.${PATCH}"
  fi
fi
VERSION_HEADER="${NEXT_TAG:-[Unreleased]}"

# ── render ────────────────────────────────────────────────────────────────────
generate_changelog() {
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo "This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format."
  echo ""
  echo "---"
  echo ""
  echo "## ${VERSION_HEADER} — ${TODAY}"
  echo ""
  echo "> Changes ${SINCE_LABEL}. ${#COMMITS[@]} commit(s) total."
  echo ""

  for CAT in Added Fixed Changed Removed; do
    # Use indirect variable reference (bash 3.2 compatible)
    VAR="BUCKET_${CAT}"
    CONTENT="${!VAR}"
    if [[ -n "$CONTENT" ]]; then
      echo "### ${CAT}"
      echo ""
      printf "%s" "$CONTENT"
      echo ""
    fi
  done
}

if $DRY_RUN; then
  generate_changelog
else
  generate_changelog > "$OUTPUT"
  echo "Wrote ${OUTPUT} (${#COMMITS[@]} commits, ${SINCE_LABEL})" >&2
fi
