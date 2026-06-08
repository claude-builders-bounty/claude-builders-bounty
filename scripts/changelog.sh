#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${CHANGELOG_OUTPUT:-CHANGELOG.md}"
REPO_URL="${CHANGELOG_REPO_URL:-}"

usage() {
  cat <<'EOF'
Usage: bash scripts/changelog.sh [--output CHANGELOG.md] [--repo-url URL]

Generates a structured CHANGELOG.md from commits since the latest git tag.

Options:
  --output FILE     Write the changelog to FILE. Defaults to CHANGELOG.md.
  --repo-url URL    Override the repository URL used for comparison links.
  -h, --help        Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      [[ $# -ge 2 ]] || { echo "Missing value for --output" >&2; exit 2; }
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --repo-url)
      [[ $# -ge 2 ]] || { echo "Missing value for --repo-url" >&2; exit 2; }
      REPO_URL="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

require_git_repo() {
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "This command must run inside a git repository." >&2
    exit 1
  fi
}

latest_tag() {
  git describe --tags --abbrev=0 2>/dev/null || true
}

normalize_repo_url() {
  local url="$1"
  url="${url%.git}"
  if [[ "$url" =~ ^git@github.com:(.+)$ ]]; then
    url="https://github.com/${BASH_REMATCH[1]}"
  fi
  printf '%s' "$url"
}

commit_range() {
  local tag="$1"
  if [[ -n "$tag" ]]; then
    printf '%s..HEAD' "$tag"
  else
    printf 'HEAD'
  fi
}

category_for_subject() {
  local subject="$1"
  local lowered
  lowered="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  if [[ "$subject" == *"!"* ]] || [[ "$lowered" == *"breaking change"* ]]; then
    printf 'Changed'
  elif [[ "$lowered" =~ ^(feat|feature|add)(\(.+\))?: ]] || [[ "$lowered" =~ ^(add|adds|added)[[:space:]] ]]; then
    printf 'Added'
  elif [[ "$lowered" =~ ^(fix|bugfix|hotfix)(\(.+\))?: ]] || [[ "$lowered" =~ ^(fix|fixes|fixed|repair|repairs)[[:space:]] ]]; then
    printf 'Fixed'
  elif [[ "$lowered" =~ ^(remove|removed|delete|deleted|drop|dropped)(\(.+\))?: ]] || [[ "$lowered" =~ ^(remove|removed|delete|deleted|drop|dropped)[[:space:]] ]]; then
    printf 'Removed'
  elif [[ "$lowered" =~ ^(refactor|perf|style|docs|test|chore|ci|build)(\(.+\))?: ]] || [[ "$lowered" =~ ^(change|changes|changed|update|updates|updated|replace|replaces)[[:space:]] ]]; then
    printf 'Changed'
  else
    printf 'Changed'
  fi
}

strip_conventional_prefix() {
  local subject="$1"
  subject="$(printf '%s' "$subject" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"
  subject="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//')"
  subject="$(printf '%s' "$subject" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"
  printf '%s' "$subject"
}

append_items() {
  local title="$1"
  local items="$2"
  local trailing_newline="${3:-1}"

  printf '### %s\n\n' "$title"
  if [[ -z "$items" ]]; then
    printf -- '- None'
  else
    printf '%s' "${items%$'\n'}"
  fi

  if [[ "$trailing_newline" == "1" ]]; then
    printf '\n\n'
  else
    printf '\n'
  fi
}

require_git_repo

TAG="$(latest_tag)"
RANGE="$(commit_range "$TAG")"
if [[ -z "$REPO_URL" ]]; then
  REPO_URL="$(git config --get remote.origin.url || true)"
fi
REPO_URL="$(normalize_repo_url "$REPO_URL")"
GENERATED_DATE="$(date +%Y-%m-%d)"

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS=$'\t' read -r sha subject; do
  [[ -n "$sha" ]] || continue
  clean_subject="$(strip_conventional_prefix "$subject")"
  [[ -n "$clean_subject" ]] || clean_subject="$subject"
  if [[ -n "$REPO_URL" ]]; then
    line="- ${clean_subject} ([${sha}](${REPO_URL}/commit/${sha}))"
  else
    line="- ${clean_subject} (${sha})"
  fi

  case "$(category_for_subject "$subject")" in
    Added) ADDED+="${line}"$'\n' ;;
    Fixed) FIXED+="${line}"$'\n' ;;
    Removed) REMOVED+="${line}"$'\n' ;;
    *) CHANGED+="${line}"$'\n' ;;
  esac
done < <(git log "$RANGE" --no-merges --pretty=format:'%h%x09%s'; printf '\n')

{
  printf '# Changelog\n\n'
  printf 'Generated on %s from commits ' "$GENERATED_DATE"
  if [[ -n "$TAG" ]]; then
    printf 'since `%s`.\n\n' "$TAG"
    if [[ -n "$REPO_URL" ]]; then
      printf '[Compare changes](%s/compare/%s...HEAD)\n\n' "$REPO_URL" "$TAG"
    fi
  else
    printf 'across the full repository history because no tags were found.\n\n'
  fi

  append_items "Added" "$ADDED"
  append_items "Fixed" "$FIXED"
  append_items "Changed" "$CHANGED"
  append_items "Removed" "$REMOVED" 0
} > "$OUTPUT_FILE"

echo "Wrote $OUTPUT_FILE"
