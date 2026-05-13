#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
FETCH_TAGS=1

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [--output FILE] [--no-fetch]

Generate a structured CHANGELOG.md from commits since the latest git tag.

Options:
  --output FILE  Write the changelog to FILE instead of CHANGELOG.md
  --no-fetch     Do not fetch tags from origin before generating
  -h, --help     Show this help message
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --output)
      if [ "$#" -lt 2 ]; then
        echo "error: --output requires a file path" >&2
        exit 1
      fi
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --no-fetch)
      FETCH_TAGS=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

if [ "$FETCH_TAGS" -eq 1 ] && git remote get-url origin >/dev/null 2>&1; then
  git fetch --tags --quiet origin || echo "warning: could not fetch tags from origin; using local tags" >&2
fi

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$LAST_TAG" ]; then
  RANGE="$LAST_TAG..HEAD"
  RANGE_LABEL="since $LAST_TAG"
else
  RANGE="HEAD"
  RANGE_LABEL="from the full git history (no tags found)"
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

ADDED_FILE="$TMP_DIR/added.md"
FIXED_FILE="$TMP_DIR/fixed.md"
CHANGED_FILE="$TMP_DIR/changed.md"
REMOVED_FILE="$TMP_DIR/removed.md"
touch "$ADDED_FILE" "$FIXED_FILE" "$CHANGED_FILE" "$REMOVED_FILE"

repo_url() {
  local remote
  remote="$(git config --get remote.origin.url || true)"
  case "$remote" in
    git@github.com:*)
      remote="https://github.com/${remote#git@github.com:}"
      ;;
    https://github.com/*)
      ;;
    *)
      echo ""
      return
      ;;
  esac
  remote="${remote%.git}"
  echo "$remote"
}

commit_link() {
  local repo="$1"
  local full_hash="$2"
  local short_hash="$3"
  if [ -n "$repo" ]; then
    printf "[%s](%s/commit/%s)" "$short_hash" "$repo" "$full_hash"
  else
    printf "%s" "$short_hash"
  fi
}

clean_subject() {
  local subject="$1"
  subject="$(printf "%s" "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//')"
  subject="$(printf "%s" "$subject" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"
  printf "%s" "$subject"
}

category_for_subject() {
  local subject lower
  subject="$1"
  lower="$(printf "%s" "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|deprecate:*|deprecated:*|remove\ *|removed\ *|delete\ *|deleted\ *|drop\ *|dropped\ *)
      echo "Removed"
      ;;
    fix:*|fixed:*|bugfix:*|hotfix:*|repair:*|patch:*|resolve:*|resolved:*|fixes\ *|fixed\ *|repair\ *|resolve\ *|resolved\ *)
      echo "Fixed"
      ;;
    feat:*|feature:*|add:*|added:*|implement:*|implemented:*|introduce:*|introduced:*|create:*|created:*|new\ *|add\ *|added\ *|implement\ *|implemented\ *|introduce\ *|introduced\ *|create\ *|created\ *)
      echo "Added"
      ;;
    refactor:*|perf:*|performance:*|style:*|docs:*|doc:*|test:*|tests:*|ci:*|build:*|chore:*|change:*|changed:*|update:*|updated:*|improve:*|improved:*)
      echo "Changed"
      ;;
    *)
      echo "Changed"
      ;;
  esac
}

append_entry() {
  local category="$1"
  local entry="$2"
  case "$category" in
    Added) printf "%s\n" "$entry" >> "$ADDED_FILE" ;;
    Fixed) printf "%s\n" "$entry" >> "$FIXED_FILE" ;;
    Changed) printf "%s\n" "$entry" >> "$CHANGED_FILE" ;;
    Removed) printf "%s\n" "$entry" >> "$REMOVED_FILE" ;;
  esac
}

REPO_URL="$(repo_url)"
COMMIT_COUNT=0

while IFS=$'\037' read -r full_hash short_hash subject author date || [ -n "${full_hash:-}" ]; do
  [ -n "${full_hash:-}" ] || continue
  COMMIT_COUNT=$((COMMIT_COUNT + 1))
  display_subject="$(clean_subject "$subject")"
  [ -n "$display_subject" ] || display_subject="$subject"
  category="$(category_for_subject "$subject")"
  if [ "$category" = "Changed" ]; then
    category="$(category_for_subject "$display_subject")"
  fi
  link="$(commit_link "$REPO_URL" "$full_hash" "$short_hash")"
  append_entry "$category" "- $display_subject ($link, $date, $author)"
done < <(git log --no-merges --date=short --pretty=format:'%H%x1f%h%x1f%s%x1f%an%x1f%ad' "$RANGE")

if [ "$COMMIT_COUNT" -eq 1 ]; then
  COMMIT_WORD="commit"
else
  COMMIT_WORD="commits"
fi

{
  printf "# Changelog\n\n"
  printf "Generated on %s using %s %s.\n\n" "$(date +%Y-%m-%d)" "$COMMIT_WORD" "$RANGE_LABEL"
  printf "## Unreleased\n\n"

  for section in Added Fixed Changed Removed; do
    case "$section" in
      Added) file="$ADDED_FILE" ;;
      Fixed) file="$FIXED_FILE" ;;
      Changed) file="$CHANGED_FILE" ;;
      Removed) file="$REMOVED_FILE" ;;
    esac

    printf "### %s\n" "$section"
    if [ -s "$file" ]; then
      sort -u "$file"
    else
      printf "%s\n" "- No changes."
    fi
    printf "\n"
  done
} > "$OUTPUT_FILE"

echo "Wrote $OUTPUT_FILE with $COMMIT_COUNT $COMMIT_WORD $RANGE_LABEL."
