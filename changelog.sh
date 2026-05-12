#!/usr/bin/env bash
set -eo pipefail

OUTPUT_FILE="CHANGELOG.md"
REPO_DIR="."
TAG=""

usage() {
  cat <<'EOF'
Usage: bash changelog.sh [--repo <path>] [--output <file>] [--tag <git-tag>]

Generate a Keep a Changelog style CHANGELOG.md from git history.
- Uses commits since the most recent git tag by default
- Falls back to the full history when no tag exists
- Auto-categorizes commits into Added / Fixed / Changed / Removed
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO_DIR="${2:?missing repo path}"
      shift 2
      ;;
    --output)
      OUTPUT_FILE="${2:?missing output path}"
      shift 2
      ;;
    --tag)
      TAG="${2:?missing tag value}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

require_git_repo() {
  git -C "$REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
    echo "Not a git repository: $REPO_DIR" >&2
    exit 1
  }
}

trim() {
  local value="$1"
  value="${value#${value%%[![:space:]]*}}"
  value="${value%${value##*[![:space:]]}}"
  printf '%s' "$value"
}

escape_markdown() {
  printf '%s' "$1" | sed 's/|/\\|/g'
}

categorize_commit() {
  local subject lower
  subject="$1"
  lower=$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')

  if [[ "$lower" =~ ^(feat|feature)(\(.+\))?: ]] || [[ "$lower" =~ \b(add|adds|added|new|introduce|introduced|create|created|support)\b ]]; then
    printf 'Added'
  elif [[ "$lower" =~ ^(fix|bugfix|hotfix)(\(.+\))?: ]] || [[ "$lower" =~ \b(fix|fixed|bug|bugs|resolve|resolved|patch|patched)\b ]]; then
    printf 'Fixed'
  elif [[ "$lower" =~ ^(remove|revert)(\(.+\))?: ]] || [[ "$lower" =~ \b(remove|removed|delete|deleted|drop|dropped|deprecat|retire)\b ]]; then
    printf 'Removed'
  else
    printf 'Changed'
  fi
}

clean_subject() {
  local subject="$1"
  subject=$(printf '%s' "$subject" | sed -E 's/^(feat|feature|fix|bugfix|hotfix|docs|doc|style|refactor|perf|test|build|ci|chore|remove|revert)(\([^)]*\))?!?:[[:space:]]*//I')
  subject=$(trim "$subject")
  printf '%s' "$subject"
}

require_git_repo

if [[ -z "$TAG" ]]; then
  TAG=$(git -C "$REPO_DIR" describe --tags --abbrev=0 2>/dev/null || true)
fi

if [[ -n "$TAG" ]]; then
  RANGE="$TAG..HEAD"
else
  RANGE="HEAD"
fi

REMOTE_URL=$(git -C "$REPO_DIR" config --get remote.origin.url || true)
REPO_WEB_URL=""
if [[ -n "$REMOTE_URL" ]]; then
  REPO_WEB_URL=$(printf '%s' "$REMOTE_URL" | sed -E 's#git@github.com:#https://github.com/#; s#\.git$##')
fi

COMMITS=()
while IFS=$'\t' read -r sha subject; do
  [[ -z "${sha:-}" ]] && continue
  COMMITS+=("${sha}"$'\t'"${subject}")
done < <(git -C "$REPO_DIR" log --reverse --format='%H%x09%s' "$RANGE")

added=()
fixed=()
changed=()
removed=()

for line in "${COMMITS[@]}"; do
  [[ -z "$line" ]] && continue
  sha=${line%%$'\t'*}
  subject=${line#*$'\t'}
  clean=$(clean_subject "$subject")
  clean=$(escape_markdown "$clean")
  short_sha=$(git -C "$REPO_DIR" rev-parse --short "$sha")

  if [[ -n "$REPO_WEB_URL" ]]; then
    entry="- ${clean} ([\`${short_sha}\`](${REPO_WEB_URL}/commit/${sha}))"
  else
    entry="- ${clean} (\`${short_sha}\`)"
  fi

  case "$(categorize_commit "$subject")" in
    Added) added+=("$entry") ;;
    Fixed) fixed+=("$entry") ;;
    Changed) changed+=("$entry") ;;
    Removed) removed+=("$entry") ;;
  esac
done

mkdir -p "$(dirname "$OUTPUT_FILE")"

{
  echo '# Changelog'
  echo
  echo 'All notable changes to this project will be documented in this file.'
  echo
  echo 'The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).'
  echo
  if [[ -n "$TAG" ]]; then
    echo "Generated from commits after tag \`$TAG\`."
  else
    echo 'Generated from the complete git history because no tag was found.'
  fi
  echo
  echo '## [Unreleased]'
  echo

  print_section() {
    local title="$1"
    shift
    local -a lines=("$@")
    [[ ${#lines[@]} -eq 0 ]] && return 0
    echo "### $title"
    for entry in "${lines[@]}"; do
      echo "$entry"
    done
    echo
  }

  if [[ ${#COMMITS[@]} -eq 0 ]]; then
    echo '_No changes detected since the selected tag._'
    echo
  else
    print_section 'Added' "${added[@]}"
    print_section 'Fixed' "${fixed[@]}"
    print_section 'Changed' "${changed[@]}"
    print_section 'Removed' "${removed[@]}"
  fi
} > "$OUTPUT_FILE"

echo "Generated $OUTPUT_FILE from ${#COMMITS[@]} commits (${TAG:-no tag found})"
