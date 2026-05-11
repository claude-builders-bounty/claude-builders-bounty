#!/usr/bin/env bash
set -euo pipefail

# Generate a structured CHANGELOG.md from git commits since the latest tag.
# Zero dependencies beyond git + POSIX coreutils.
# Usage: bash changelog.sh [--output CHANGELOG.md] [--since-tag TAG] [--dry-run]

OUT="CHANGELOG.md"
SINCE_TAG=""
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: bash changelog.sh [options]

Options:
  -o, --output FILE     Write changelog to FILE (default: CHANGELOG.md)
  --since-tag TAG       Use TAG as the start of the git range instead of auto-detecting latest tag
  --dry-run             Print generated changelog to stdout instead of writing a file
  -h, --help            Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      [[ $# -ge 2 ]] || { echo "Error: $1 requires a file path." >&2; exit 2; }
      OUT="$2"
      shift 2
      ;;
    --since-tag)
      [[ $# -ge 2 ]] || { echo "Error: --since-tag requires a tag name." >&2; exit 2; }
      SINCE_TAG="$2"
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
      echo "Error: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: run this script inside a git repository." >&2
  exit 1
fi

if [[ -n "$SINCE_TAG" ]]; then
  if ! git rev-parse --verify --quiet "refs/tags/${SINCE_TAG}" >/dev/null; then
    echo "Error: tag not found: ${SINCE_TAG}" >&2
    exit 1
  fi
  latest_tag="$SINCE_TAG"
elif latest_tag=$(git describe --tags --abbrev=0 2>/dev/null); then
  :
else
  latest_tag=""
fi

if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  since_label="since ${latest_tag}"
else
  range="HEAD"
  since_label="from repository history"
fi

if [[ -z "$(git log --format=%H "$range" 2>/dev/null)" ]]; then
  echo "No commits found ${since_label}." >&2
  exit 0
fi

date_utc="$(date -u +%Y-%m-%d)"
repo_url="$(git config --get remote.origin.url || true)"
repo_url="${repo_url%.git}"
if [[ "$repo_url" == git@github.com:* ]]; then
  repo_url="https://github.com/${repo_url#git@github.com:}"
elif [[ "$repo_url" == https://github.com/* ]]; then
  :
else
  repo_url=""
fi

strip_prefix() {
  local subject="$1"
  # Remove common conventional commit prefixes while preserving readable text.
  printf '%s' "$subject" | sed -E 's/^(feat|feature|fix|bugfix|bug|docs|doc|refactor|perf|performance|style|test|tests|ci|build|chore|change|changed|remove|removed|delete|deleted|revert)(\([^)]+\))?!?:[[:space:]]*//I'
}

append_entry() {
  local file="$1"
  local line="$2"
  printf '%s\n' "$line" >> "$file"
}

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT
added_file="$workdir/added"
fixed_file="$workdir/fixed"
changed_file="$workdir/changed"
removed_file="$workdir/removed"
breaking_file="$workdir/breaking"
: > "$added_file"; : > "$fixed_file"; : > "$changed_file"; : > "$removed_file"; : > "$breaking_file"

while IFS=$'\t' read -r hash subject body || [[ -n "${hash:-}" ]]; do
  [[ -n "${hash:-}" ]] || continue
  lower="$(printf '%s' "$subject $body" | tr '[:upper:]' '[:lower:]')"
  clean_subject="$(strip_prefix "$subject")"
  [[ -n "$clean_subject" ]] || clean_subject="$subject"

  if [[ -n "$repo_url" ]]; then
    entry="- ${clean_subject} ([${hash}](${repo_url}/commit/${hash}))"
  else
    entry="- ${clean_subject} (${hash})"
  fi

  # BREAKING CHANGE gets highlighted but still also lands in its functional category.
  if [[ "$subject" == *"!:"* || "$lower" == *"breaking change"* ]]; then
    append_entry "$breaking_file" "$entry"
  fi

  case "$lower" in
    feat:*|feature:*|feat\(*|feature\(*|add:*|added:*|add\ *|adds\ *|*" add "*|*" adds "*|*" new "*)
      append_entry "$added_file" "$entry" ;;
    fix:*|fixed:*|bugfix:*|bug:*|fix\ *|fixes\ *|*" fix "*|*" fixes "*|*" bug "*|*" regression "*)
      append_entry "$fixed_file" "$entry" ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|remove\ *|delete\ *|drop\ *|*" remove "*|*" delete "*|*" dropped "*)
      append_entry "$removed_file" "$entry" ;;
    *)
      append_entry "$changed_file" "$entry" ;;
  esac
done < <(git log --no-merges --reverse --pretty=format:'%h%x09%s%x09%b' "$range")

write_section() {
  local title="$1"
  local file="$2"
  printf '### %s\n' "$title"
  if [[ -s "$file" ]]; then
    cat "$file"
    printf '\n\n'
  else
    printf -- '- None\n\n'
  fi
}

new_content="$workdir/new_changelog.md"
{
  printf '# Changelog\n\n'
  printf 'All notable changes to this project will be documented in this file.\n\n'
  printf '## [Unreleased] - %s\n\n' "$date_utc"
  printf '_Generated from git history %s._\n\n' "$since_label"
  if [[ -s "$breaking_file" ]]; then
    write_section "Breaking Changes" "$breaking_file"
  fi
  write_section "Added" "$added_file"
  write_section "Fixed" "$fixed_file"
  write_section "Changed" "$changed_file"
  write_section "Removed" "$removed_file"
} > "$new_content"

# Preserve older release sections below the newly generated Unreleased section.
if [[ "$DRY_RUN" -eq 0 && -f "$OUT" ]]; then
  awk 'BEGIN{seen=0} /^## \[/{seen=1} seen{print}' "$OUT" >> "$new_content" || true
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  cat "$new_content"
else
  mv "$new_content" "$OUT"
  echo "Wrote ${OUT} (${since_label})."
fi
