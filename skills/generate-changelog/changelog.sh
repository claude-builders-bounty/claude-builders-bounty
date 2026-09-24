#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history.
set -euo pipefail

REPO_ROOT="."
OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""
VERSION_OVERRIDE=""
PREVIEW=0
APPEND=0

usage() {
  cat <<'EOF'
Usage: bash changelog.sh [options] [repo-root]

Options:
  --since <tag>      Start from a specific tag (default: nearest first-parent tag)
  --version <name>   Override release version in the header (e.g. 1.2.0)
  --output <file>    Output file (default: CHANGELOG.md)
  --preview          Print changelog to stdout without writing a file
  --append           Prepend the new release to an existing CHANGELOG.md
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
    --append)
      APPEND=1
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

if ! git rev-parse --verify 'HEAD^{commit}' >/dev/null 2>&1; then
  echo "Error: repository has no commits" >&2
  exit 1
fi

# A shallow clone cannot establish the actual last release boundary.
if [[ "$(git rev-parse --is-shallow-repository)" == "true" ]]; then
  echo "Error: shallow history is incomplete; fetch full history and tags before generating a changelog" >&2
  exit 1
fi

if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG="$(git describe --first-parent --tags --abbrev=0 2>/dev/null || true)"
fi

if [[ -n "$SINCE_TAG" ]]; then
  if ! git rev-parse --verify "${SINCE_TAG}^{commit}" >/dev/null 2>&1; then
    echo "Error: --since does not resolve to a commit: ${SINCE_TAG}" >&2
    exit 1
  fi
  if ! git merge-base --is-ancestor "$SINCE_TAG" HEAD; then
    echo "Error: --since is not an ancestor of HEAD: ${SINCE_TAG}" >&2
    exit 1
  fi
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
  [Breaking]=""
  [Uncategorized]=""
)

commit_type() {
  local subject type
  subject="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  type="$(printf '%s' "$subject" | sed -E 's/^([a-z]+)(\([^)]*\))?!?:.*$/\1/')"
  if [[ "$type" == "$subject" ]]; then
    type="${subject%% *}"
  fi
  printf '%s' "$type"
}

is_breaking_change() {
  local subject="$1"
  if printf '%s' "$subject" | grep -Eq '^[a-zA-Z]+(\([^)]*\))?!'; then
    return 0
  fi
  if printf '%s' "$subject" | grep -Eq '[Bb][Rr][Ee][Aa][Kk][Ii][Nn][Gg][[:space:]]+[Cc][Hh][Aa][Nn][Gg][Ee]'; then
    return 0
  fi
  return 1
}

categorize() {
  local type
  type="$(commit_type "$1")"
  case "$type" in
    feat|feature|add|implement|create|new) printf 'Added' ;;
    fix|bugfix|bug|hotfix|patch|resolve) printf 'Fixed' ;;
    remove|delete|deprecate|drop) printf 'Removed' ;;
    update|change|refactor|migrate|perf|docs|chore|ci|test) printf 'Changed' ;;
    *) printf 'Uncategorized' ;;
  esac
}

clean_subject() {
  local subject="$1"
  printf '%s' "$subject" \
    | sed -E 's/^(feat|feature|add|implement|create|new|fix|bugfix|bug|hotfix|patch|resolve|update|change|refactor|migrate|perf|remove|delete|deprecate|drop|docs|chore|ci|test)(\([^)]+\))?!?:[[:space:]]*//I' \
    | sed 's/[[:space:]]*$//' \
    | sed 's/\.$//'
}

git_log=(git log --pretty=format:'%h %s' --no-merges)
if [[ -n "$RANGE" ]]; then
  git_log+=("$RANGE")
fi

# Capture and check the history read before touching any output file.
# Process substitution hides the producer exit status from the read loop.
if ! history_text="$("${git_log[@]}")"; then
  echo "Error: unable to read Git history; changelog output was not written" >&2
  exit 1
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
  if is_breaking_change "$subject"; then
    SECTIONS[Breaking]+="- ${clean} (${hash:0:7})"$'\n'
  fi
  SECTIONS[$section]+="- ${clean} (${hash:0:7})"$'\n'
done <<< "$history_text"

render_release() {
  printf '## [%s] - %s\n\n' "$VERSION" "$DATE"
  for section in Breaking Added Fixed Changed Removed Uncategorized; do
    if [[ -n "${SECTIONS[$section]}" ]]; then
      printf '### %s\n\n' "$section"
      if [[ "$section" == "Uncategorized" ]]; then
        printf '%s\n\n' 'Review these commits manually: no recognized category was found.'
      fi
      printf '%s' "${SECTIONS[$section]}"
      printf '\n'
    fi
  done
}

render_changelog() {
  printf '# Changelog\n\n'
  render_release
}

write_changelog() {
  local release_file
  release_file="$(mktemp)"
  render_release >"$release_file"

  if [[ "$APPEND" -eq 1 && -f "$OUTPUT_FILE" ]]; then
    if grep -q '^# Changelog' "$OUTPUT_FILE"; then
      {
        printf '# Changelog\n\n'
        cat "$release_file"
        awk -v target="## [$VERSION]" '
          BEGIN { after_title=0; skip_release=0 }
          /^# Changelog$/ { after_title=1; next }
          after_title && NF==0 { after_title=0; next }
          index($0, target) == 1 { skip_release=1; next }
          skip_release && /^## \[/ { skip_release=0 }
          !skip_release { print }
        ' "$OUTPUT_FILE"
      } >"${OUTPUT_FILE}.tmp"
      mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
    else
      {
        printf '# Changelog\n\n'
        cat "$release_file"
        cat "$OUTPUT_FILE"
      } >"${OUTPUT_FILE}.tmp"
      mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
    fi
    rm -f "$release_file"
    echo "Appended release to ${OUTPUT_FILE} (${commit_count} commits)"
  else
    render_changelog >"$OUTPUT_FILE"
    rm -f "$release_file"
    echo "Wrote ${OUTPUT_FILE} (${commit_count} commits)"
  fi
}

if [[ "$PREVIEW" -eq 1 ]]; then
  render_changelog
  echo "Previewed ${commit_count} commits (stdout only)" >&2
else
  write_changelog
fi
