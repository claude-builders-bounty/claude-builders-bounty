#!/usr/bin/env bash
set -euo pipefail

OUTPUT_PATH="${1:-CHANGELOG.md}"
REPO_PATH="${2:-.}"

die() {
  printf 'changelog.sh: %s\n' "$1" >&2
  exit 1
}

command -v git >/dev/null 2>&1 || die "git is required"

git -C "$REPO_PATH" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
  || die "$REPO_PATH is not a git repository"

REPO_ROOT="$(git -C "$REPO_PATH" rev-parse --show-toplevel)"
LAST_TAG="$(git -C "$REPO_ROOT" describe --tags --abbrev=0 2>/dev/null || true)"
TODAY="$(date +%F)"

if [ -n "$LAST_TAG" ]; then
  RANGE="$LAST_TAG..HEAD"
  RANGE_NOTE="Changes since \`$LAST_TAG\`."
else
  RANGE="HEAD"
  RANGE_NOTE="No git tags were found; generated from the full commit history."
fi

REMOTE_URL="$(git -C "$REPO_ROOT" config --get remote.origin.url 2>/dev/null || true)"
REMOTE_URL="${REMOTE_URL%.git}"

github_url() {
  case "$REMOTE_URL" in
    https://github.com/*)
      printf '%s' "$REMOTE_URL"
      ;;
    git@github.com:*)
      printf 'https://github.com/%s' "${REMOTE_URL#git@github.com:}"
      ;;
    ssh://git@github.com/*)
      printf 'https://github.com/%s' "${REMOTE_URL#ssh://git@github.com/}"
      ;;
    *)
      printf ''
      ;;
  esac
}

GITHUB_URL="$(github_url)"

category_for() {
  subject="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  prefix="${subject%%:*}"
  prefix="${prefix%%!*}"
  prefix="${prefix%%(*}"
  first_word="${subject%% *}"
  first_word="${first_word%%:*}"
  first_word="${first_word%%(*}"

  case "$prefix" in
    feat|feature|add|added|new) printf 'Added'; return ;;
    fix|bugfix|bug|patch|hotfix) printf 'Fixed'; return ;;
    remove|removed|delete|deleted|drop|dropped) printf 'Removed'; return ;;
    change|changed|refactor|perf|performance|style|docs|doc|test|tests|build|ci|chore|deps|dependency|maintenance) printf 'Changed'; return ;;
  esac

  case "$first_word" in
    add|added|adds|new|create|created) printf 'Added' ;;
    fix|fixed|fixes|bugfix|repair|resolved) printf 'Fixed' ;;
    remove|removed|removes|delete|deleted|drop|dropped) printf 'Removed' ;;
    *) printf 'Changed' ;;
  esac
}

clean_subject() {
  subject="$1"
  case "$subject" in
    *:*)
      prefix="${subject%%:*}"
      normalized="$(printf '%s' "$prefix" | tr '[:upper:]' '[:lower:]')"
      normalized="${normalized%%!*}"
      normalized="${normalized%%(*}"
      case "$normalized" in
        feat|feature|add|added|new|fix|bugfix|bug|patch|hotfix|remove|removed|delete|deleted|drop|dropped|change|changed|refactor|perf|performance|style|docs|doc|test|tests|build|ci|chore|deps|dependency|maintenance)
          subject="${subject#*:}"
          ;;
      esac
      ;;
  esac

  subject="${subject#"${subject%%[![:space:]]*}"}"
  subject="${subject%"${subject##*[![:space:]]}"}"
  printf '%s' "$subject"
}

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

ADDED="$tmpdir/added"
FIXED="$tmpdir/fixed"
CHANGED="$tmpdir/changed"
REMOVED="$tmpdir/removed"
touch "$ADDED" "$FIXED" "$CHANGED" "$REMOVED"

while IFS="$(printf '\t')" read -r hash subject; do
  [ -n "${hash:-}" ] || continue
  category="$(category_for "$subject")"
  message="$(clean_subject "$subject")"
  short_hash="$(printf '%s' "$hash" | cut -c1-7)"

  if [ -n "$GITHUB_URL" ]; then
    entry="- ${message} ([\`${short_hash}\`](${GITHUB_URL}/commit/${hash}))"
  else
    entry="- ${message} (\`${short_hash}\`)"
  fi

  case "$category" in
    Added) printf '%s\n' "$entry" >> "$ADDED" ;;
    Fixed) printf '%s\n' "$entry" >> "$FIXED" ;;
    Changed) printf '%s\n' "$entry" >> "$CHANGED" ;;
    Removed) printf '%s\n' "$entry" >> "$REMOVED" ;;
  esac
done < <(git -C "$REPO_ROOT" log --reverse --no-merges --format='%H%x09%s' "$RANGE")

write_section() {
  title="$1"
  file="$2"

  printf '### %s\n\n' "$title"
  if [ -s "$file" ]; then
    cat "$file"
  else
    printf '_No changes detected._\n'
  fi
  printf '\n'
}

mkdir -p "$(dirname "$OUTPUT_PATH")"

{
  printf '# Changelog\n\n'
  printf 'All notable changes generated from git history.\n\n'
  printf '## Unreleased - %s\n\n' "$TODAY"
  printf '_%s_\n\n' "$RANGE_NOTE"
  write_section "Added" "$ADDED"
  write_section "Fixed" "$FIXED"
  write_section "Changed" "$CHANGED"
  write_section "Removed" "$REMOVED"
} > "$OUTPUT_PATH"

printf 'Generated %s from %s\n' "$OUTPUT_PATH" "$RANGE_NOTE"
