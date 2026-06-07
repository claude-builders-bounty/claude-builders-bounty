#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history.
set -euo pipefail

REPO_ROOT="."
OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""
VERSION_OVERRIDE=""
PREVIEW=0

usage() {
  cat <<'EOF'
Usage: bash changelog.sh [options] [repo-root]

Options:
  --since <tag>      Start from a specific tag (default: latest tag)
  --version <name>   Override release version in the header (e.g. 1.2.0)
  --output <file>    Output file (default: CHANGELOG.md)
  --preview          Print changelog to stdout without writing a file
  -h, --help         Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since)
      SINCE_TAG="${2:-}"
      shift 2
      ;;
    --version)
      VERSION_OVERRIDE="${2:-}"
      shift 2
      ;;
    --output)
      OUTPUT_FILE="${2:-}"
      shift 2
      ;;
    --preview)
      PREVIEW=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      REPO_ROOT="$1"
      shift
      ;;
  esac
done

cd "$REPO_ROOT"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: not a git repository" >&2
  exit 1
fi

if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [[ -n "$SINCE_TAG" ]]; then
  RANGE="${SINCE_TAG}..HEAD"
  VERSION="${VERSION_OVERRIDE:-${SINCE_TAG}-next}"
  [[ "$PREVIEW" -eq 0 ]] && echo "Generating changelog since ${SINCE_TAG}" >&2
else
  RANGE=""
  VERSION="${VERSION_OVERRIDE:-Unreleased}"
  [[ "$PREVIEW" -eq 0 ]] && echo "Generating changelog from full history (no tags found)" >&2
fi

DATE="$(date -u +%Y-%m-%d)"
declare -A SECTIONS=(
  [Added]=""
  [Fixed]=""
  [Changed]=""
  [Removed]=""
)

commit_type() {
  local subject type
  subject="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  type="$(printf '%s' "$subject" | sed -E 's/^([a-z]+)(\([^)]*\))?:.*$/\1/')"
  if [[ "$type" == "$subject" ]]; then
    type="${subject%% *}"
  fi
  printf '%s' "$type"
}

categorize() {
  local type
  type="$(commit_type "$1")"
  case "$type" in
    feat|feature|add|implement|create|new) printf 'Added' ;;
    fix|bugfix|bug|hotfix|patch|resolve) printf 'Fixed' ;;
    remove|delete|deprecate|drop) printf 'Removed' ;;
    *) printf 'Changed' ;;
  esac
}

clean_subject() {
  local subject="$1"
  printf '%s' "$subject" \
    | sed -E 's/^(feat|feature|add|implement|create|fix|bugfix|hotfix|patch|resolve|update|change|refactor|migrate|perf|remove|delete|deprecate|docs|chore|ci|test)(\([^)]+\))?:?[[:space:]]*//I' \
    | sed 's/[[:space:]]*$//' \
    | sed 's/\.$//'
}

git_log=(git log --pretty=format:'%h %s' --no-merges)
if [[ -n "$RANGE" ]]; then
  git_log+=("$RANGE")
fi

commit_count=0
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  commit_count=$((commit_count + 1))
  hash="${line%% *}"
  subject="${line#* }"
  section="$(categorize "$subject")"
  clean="$(clean_subject "$subject")"
  [[ -z "$clean" ]] && clean="$subject"
  SECTIONS[$section]+="- ${clean} (${hash:0:7})"$'\n'
done < <("${git_log[@]}" 2>/dev/null; echo)

render_changelog() {
  printf '# Changelog\n\n'
  printf '## [%s] - %s\n\n' "$VERSION" "$DATE"
  for section in Added Fixed Changed Removed; do
    if [[ -n "${SECTIONS[$section]}" ]]; then
      printf '### %s\n\n' "$section"
      printf '%b' "${SECTIONS[$section]}"
      printf '\n'
    fi
  done
}

if [[ "$PREVIEW" -eq 1 ]]; then
  render_changelog
  echo "Previewed ${commit_count} commits (stdout only)" >&2
else
  render_changelog >"$OUTPUT_FILE"
  echo "Wrote ${OUTPUT_FILE} (${commit_count} commits)"
fi
