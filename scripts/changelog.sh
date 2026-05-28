#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
REPO_DIR="."
SINCE_TAG=""
VERSION="Unreleased"
DRY_RUN=0

usage() {
  cat <<'USAGE'
Generate a structured CHANGELOG.md from git history.

Usage:
  bash scripts/changelog.sh [options]

Options:
  --repo <path>       Git repository to read. Defaults to current directory.
  --output <path>     Output file. Defaults to CHANGELOG.md.
  --since <tag>       Use this tag instead of auto-detecting the latest tag.
  --version <name>    Changelog section name. Defaults to Unreleased.
  --dry-run           Print changelog to stdout instead of writing a file.
  -h, --help          Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO_DIR="${2:?missing value for --repo}"
      shift 2
      ;;
    --output)
      OUTPUT_FILE="${2:?missing value for --output}"
      shift 2
      ;;
    --since)
      SINCE_TAG="${2:?missing value for --since}"
      shift 2
      ;;
    --version)
      VERSION="${2:?missing value for --version}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! git -C "$REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository: $REPO_DIR" >&2
  exit 1
fi

REPO_ROOT="$(git -C "$REPO_DIR" rev-parse --show-toplevel)"

if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG="$(git -C "$REPO_ROOT" describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [[ -n "$SINCE_TAG" ]]; then
  if ! git -C "$REPO_ROOT" rev-parse --verify --quiet "$SINCE_TAG^{commit}" >/dev/null; then
    echo "Tag not found: $SINCE_TAG" >&2
    exit 1
  fi
  RANGE="$SINCE_TAG..HEAD"
  RANGE_LABEL="since \`$SINCE_TAG\`"
else
  RANGE="HEAD"
  RANGE_LABEL="from the repository's full history because no git tag was found"
fi

DATE="$(date +%Y-%m-%d)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

ADDED="$TMP_DIR/added"
FIXED="$TMP_DIR/fixed"
CHANGED="$TMP_DIR/changed"
REMOVED="$TMP_DIR/removed"
: >"$ADDED"
: >"$FIXED"
: >"$CHANGED"
: >"$REMOVED"

normalize_subject() {
  local subject="$1"

  subject="${subject#Merge pull request }"
  subject="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//')"
  subject="$(printf '%s' "$subject" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"

  if [[ -z "$subject" ]]; then
    subject="Update project"
  fi

  printf '%s' "$subject"
}

category_for_subject() {
  local lower="$1"

  if [[ "$lower" =~ ^(remove|removed|removes|delete|deleted|deletes|drop|dropped|drops|deprecate|deprecated|deprecates)(\(|:|[[:space:]]) ]]; then
    printf 'Removed'
  elif [[ "$lower" =~ ^(fix|fixed|fixes|bugfix|hotfix|security)(\(|:|[[:space:]]) ]] \
      || [[ "$lower" =~ (fix|fixed|bug|crash|error|regression|vulnerability) ]]; then
    printf 'Fixed'
  elif [[ "$lower" =~ ^(feat|feature|add|added|adds)(\(|:|[[:space:]]) ]] \
      || [[ "$lower" =~ (add|added|adds|introduce|introduced|implement|implemented|support|create|created) ]]; then
    printf 'Added'
  else
    printf 'Changed'
  fi
}

append_entry() {
  local category="$1"
  local entry="$2"

  case "$category" in
    Added) printf '%s\n' "$entry" >>"$ADDED" ;;
    Fixed) printf '%s\n' "$entry" >>"$FIXED" ;;
    Removed) printf '%s\n' "$entry" >>"$REMOVED" ;;
    *) printf '%s\n' "$entry" >>"$CHANGED" ;;
  esac
}

while IFS=$'\x1f' read -r hash subject author commit_date || [[ -n "${hash:-}" ]]; do
  [[ -z "${hash:-}" ]] && continue

  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  category="$(category_for_subject "$lower")"
  clean_subject="$(normalize_subject "$subject")"
  short_hash="$(git -C "$REPO_ROOT" rev-parse --short "$hash")"

  append_entry "$category" "- ${clean_subject} (${short_hash}, ${commit_date}, ${author})"
done < <(git -C "$REPO_ROOT" log --no-merges --date=short --pretty=format:'%H%x1f%s%x1f%an%x1f%ad' "$RANGE")

write_category() {
  local title="$1"
  local file="$2"

  if [[ -s "$file" ]]; then
    printf '### %s\n\n' "$title"
    sort -u "$file"
    printf '\n'
  fi
}

generate_changelog() {
  cat <<HEADER
# Changelog

All notable changes are grouped from git commit history.

## [${VERSION}] - ${DATE}

Generated from commits ${RANGE_LABEL}.

HEADER

  if [[ ! -s "$ADDED" && ! -s "$FIXED" && ! -s "$CHANGED" && ! -s "$REMOVED" ]]; then
    printf 'No changes found.\n'
    return
  fi

  write_category "Added" "$ADDED"
  write_category "Fixed" "$FIXED"
  write_category "Changed" "$CHANGED"
  write_category "Removed" "$REMOVED"
}

if [[ "$DRY_RUN" -eq 1 ]]; then
  generate_changelog
else
  mkdir -p "$(dirname "$OUTPUT_FILE")"
  generate_changelog >"$OUTPUT_FILE"
  echo "Wrote $OUTPUT_FILE"
fi
