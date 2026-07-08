#!/usr/bin/env bash
set -euo pipefail

# Generate a structured CHANGELOG.md from commits since the latest reachable git tag.
# Usage: bash tools/generate-changelog/changelog.sh [repo-path] [output-file]

REPO="${1:-.}"
OUT="${2:-CHANGELOG.md}"

if ! git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: '$REPO' is not a git repository" >&2
  exit 1
fi

LAST_TAG="$(git -C "$REPO" describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$LAST_TAG" ]]; then
  RANGE="$LAST_TAG..HEAD"
  SINCE_LABEL="since $LAST_TAG"
else
  RANGE="HEAD"
  SINCE_LABEL="from initial commit (no tags found)"
fi

RELEASE_DATE="$(date +%Y-%m-%d)"
REMOTE_URL="$(git -C "$REPO" config --get remote.origin.url 2>/dev/null || true)"
GITHUB_REPO=""
if [[ "$REMOTE_URL" =~ ^git@github\.com:(.+)\.git$ ]]; then
  GITHUB_REPO="${BASH_REMATCH[1]}"
elif [[ "$REMOTE_URL" =~ ^https://github\.com/(.+)\.git$ ]]; then
  GITHUB_REPO="${BASH_REMATCH[1]}"
elif [[ "$REMOTE_URL" =~ ^https://github\.com/(.+)$ ]]; then
  GITHUB_REPO="${BASH_REMATCH[1]}"
fi

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT
for section in Added Fixed Changed Removed; do
  : > "$TMPDIR/$section"
done

categorize() {
  local subject="$1"

  case "$subject" in
    feat:*|feat'('*'): '*|feature:*|feature'('*'): '*|add|add\ *|adds\ *|added\ *|new\ *|introduce\ *|introduced\ *)
      echo "Added"
      ;;
    fix:*|fix'('*'): '*|fixes:*|fixed:*|bug:*|bugfix:*|hotfix:*|fix\ *|fixes\ *|fixed\ *|bug\ *|bugfix\ *|hotfix\ *|*bug*|*error*|*crash*|*failure*)
      echo "Fixed"
      ;;
    remove\ *|removes\ *|removed\ *|delete\ *|deletes\ *|deleted\ *|drop\ *|drops\ *|dropped\ *|deprecate\ *|deprecated\ *|*remove*|*removed*|*delete*|*deleted*|*drop*|*dropped*|*deprecat*)
      echo "Removed"
      ;;
    *)
      echo "Changed"
      ;;
  esac
}

commit_count=0
while IFS=$'\t' read -r short_hash subject || [[ -n "${short_hash:-}" ]]; do
  [[ -z "${short_hash:-}" ]] && continue
  commit_count=$((commit_count + 1))
  section="$(categorize "$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')")"
  if [[ -n "$GITHUB_REPO" ]]; then
    printf -- '- %s ([%s](https://github.com/%s/commit/%s))\n' "$subject" "$short_hash" "$GITHUB_REPO" "$short_hash" >> "$TMPDIR/$section"
  else
    printf -- '- %s (%s)\n' "$subject" "$short_hash" >> "$TMPDIR/$section"
  fi
done < <(git -C "$REPO" log --reverse --no-merges --pretty=format:'%h%x09%s' "$RANGE")

{
  echo "# Changelog"
  echo
  echo "All notable changes generated from git history."
  echo
  echo "## [Unreleased] - $RELEASE_DATE"
  echo
  echo "_Generated from $commit_count commit(s) $SINCE_LABEL._"
  echo
  for section in Added Fixed Changed Removed; do
    echo "### $section"
    if [[ -s "$TMPDIR/$section" ]]; then
      cat "$TMPDIR/$section"
    else
      echo "- No changes."
    fi
    echo
  done
} > "$OUT"

echo "Wrote $OUT from $commit_count commit(s) $SINCE_LABEL."
