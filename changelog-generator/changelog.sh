#!/usr/bin/env bash
set -euo pipefail

OUTPUT="CHANGELOG.md"
SINCE=""
REPO_DIR="."
INCLUDE_UNTAGGED="true"

usage() {
  cat <<'USAGE'
Usage: bash changelog-generator/changelog.sh [options]

Generate a structured CHANGELOG.md from git commits since the latest tag.

Options:
  --since <ref>       Start commit/tag. Defaults to latest reachable tag.
  --output <file>     Output file. Defaults to CHANGELOG.md.
  --repo <dir>        Git repository directory. Defaults to current directory.
  --no-untagged-note  Do not mention when the repository has no tags.
  -h, --help          Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE="${2:-}"; shift 2 ;;
    --output) OUTPUT="${2:-}"; shift 2 ;;
    --repo) REPO_DIR="${2:-}"; shift 2 ;;
    --no-untagged-note) INCLUDE_UNTAGGED="false"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

cd "$REPO_DIR"
git rev-parse --is-inside-work-tree >/dev/null

if [[ -z "$SINCE" ]]; then
  if SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
    SINCE="$SINCE_TAG"
  else
    SINCE=""
  fi
fi

if [[ -n "$SINCE" ]]; then
  RANGE="$SINCE..HEAD"
  BASE_LABEL="$SINCE"
else
  RANGE="HEAD"
  BASE_LABEL="repository start"
fi

VERSION="Unreleased"
DATE_UTC=$(date -u +%Y-%m-%d)
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT

for category in Added Fixed Changed Removed; do
  : > "$WORK_DIR/$category"
done

categorize() {
  local subject="$1"
  local body="$2"
  local lower
  lower=$(printf '%s %s' "$subject" "$body" | tr '[:upper:]' '[:lower:]')

  if printf '%s' "$lower" | grep -Eq '(^|[^a-z])(remove|removed|removes|delete|deleted|deprecate|deprecated)([^a-z]|$)|^revert'; then
    echo "Removed"
  elif printf '%s' "$lower" | grep -Eq '(^|[^a-z])(fix|fixed|fixes|bug|bugfix|patch|hotfix|security|cve|vulnerability)([^a-z]|$)|^fix(\(.+\))?:'; then
    echo "Fixed"
  elif printf '%s' "$lower" | grep -Eq '(^|[^a-z])(add|added|adds|new|create|created|introduce|introduced|implement|implemented|feature)([^a-z]|$)|^feat(\(.+\))?:'; then
    echo "Added"
  else
    echo "Changed"
  fi
}

clean_subject() {
  local subject="$1"
  subject=$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//')
  subject=$(printf '%s' "$subject" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')
  printf '%s' "$subject"
}

COMMIT_COUNT=0
while IFS= read -r -d '' record; do
  [[ -z "${record:-}" ]] && continue
  sha=${record%%$'\x1f'*}
  rest=${record#*$'\x1f'}
  subject=${rest%%$'\x1f'*}
  body=${rest#*$'\x1f'}
  [[ -z "${sha:-}" || "$sha" == "$record" ]] && continue
  category=$(categorize "$subject" "${body:-}")
  clean=$(clean_subject "$subject")
  short=${sha:0:7}
  printf -- '- %s (%s)\n' "$clean" "$short" >> "$WORK_DIR/$category"
  COMMIT_COUNT=$((COMMIT_COUNT + 1))
done < <(git log -z --no-merges --pretty=format:'%H%x1f%s%x1f%b%x00' "$RANGE")

TMP=$(mktemp)
{
  printf '# Changelog\n\n'
  printf 'All notable changes are generated from git history.\n\n'
  printf '## [%s] - %s\n\n' "$VERSION" "$DATE_UTC"
  if [[ "$COMMIT_COUNT" -eq 0 ]]; then
    printf '_No commits found since %s._\n' "$BASE_LABEL"
  else
    for category in Added Fixed Changed Removed; do
      printf '### %s\n' "$category"
      if [[ -s "$WORK_DIR/$category" ]]; then
        cat "$WORK_DIR/$category"
      else
        printf '_No entries._\n'
      fi
      printf '\n'
    done
  fi
  if [[ -z "$SINCE" && "$INCLUDE_UNTAGGED" == "true" ]]; then
    printf '> Note: no git tags were found, so this changelog used the full commit history.\n'
  else
    printf '> Generated from commits since `%s`.\n' "$BASE_LABEL"
  fi
} > "$TMP"

mkdir -p "$(dirname "$OUTPUT")"
mv "$TMP" "$OUTPUT"
printf 'Generated %s from %s (%s commits)\n' "$OUTPUT" "$BASE_LABEL" "$COMMIT_COUNT"
