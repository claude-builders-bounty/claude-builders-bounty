#!/usr/bin/env bash
# changelog.sh 鈥?Generate a structured CHANGELOG.md from git history
# 
# Usage: bash changelog.sh [--output CHANGELOG.md] [--tag v1.0.0]
#
# Bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1
# Requires: git

set -euo pipefail

# 鈹€鈹€鈹€ Configuration 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
OUTPUT_FILE="${OUTPUT_FILE:-CHANGELOG.md}"
SINCE_TAG="${SINCE_TAG:-}"
PROJECT_NAME="${PROJECT_NAME:-}"
PROJECT_URL="${PROJECT_URL:-}"

# 鈹€鈹€鈹€ Parse arguments 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)   OUTPUT_FILE="$2"; shift 2 ;;
    --tag)      SINCE_TAG="$2"; shift 2 ;;
    --name)     PROJECT_NAME="$2"; shift 2 ;;
    --url)      PROJECT_URL="$2"; shift 2 ;;
    --help|-h)  echo "Usage: bash changelog.sh [--output CHANGELOG.md] [--tag v1.0.0] [--name Project] [--url https://...]"; exit 0 ;;
    *)          echo "Unknown option: $1"; exit 1 ;;
  esac
done

# 鈹€鈹€鈹€ Ensure we're in a git repo 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "鉂?Error: Not inside a git repository."
  echo "   Run this script from inside a git project."
  exit 1
fi

# 鈹€鈹€鈹€ Determine the tag range 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
if [[ -z "$SINCE_TAG" ]]; then
  # Find the most recent tag
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -n "$LATEST_TAG" ]]; then
    SINCE_TAG="$LATEST_TAG"
    echo "馃搶 Using latest tag: $SINCE_TAG"
  else
    echo "馃搶 No tags found 鈥?generating changelog from the beginning of history."
  fi
fi

# 鈹€鈹€鈹€ Build the changelog 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
generate_changelog() {
  local header="# Changelog"
  local date_str
  date_str=$(date +"%Y-%m-%d")

  if [[ -n "$PROJECT_NAME" ]]; then
    header="# $PROJECT_NAME Changelog"
  fi

  # New version header
  local version="Unreleased"
  if [[ -n "$SINCE_TAG" ]]; then
    version="$SINCE_TAG"
  fi

  cat <<EOF
$header

> Generated on $date_str

## $version

EOF

  # 鈹€鈹€鈹€ Fetch commits 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
  local range=""
  local range_desc=""
  if [[ -n "$SINCE_TAG" ]]; then
    range="${SINCE_TAG}..HEAD"
    range_desc="since $SINCE_TAG"
  else
    range="HEAD"
    range_desc="from the beginning"
  fi

  echo "<!-- Commits $range_desc -->" >> "$OUTPUT_FILE"

  # Categorize commits
  local added="" fixed="" changed="" removed="" other=""

  while IFS= read -r commit; do
    [[ -z "$commit" ]] && continue
    local hash msg
    hash=$(echo "$commit" | cut -d'|' -f1)
    msg=$(echo "$commit" | cut -d'|' -f2-)

    # Determine category based on conventional commit prefix
    local category="other"
    local clean_msg="$msg"

    if [[ "$msg" =~ ^(feat|feature|add|implement|create)(\(.*\))?!?:\ *(.+) ]]; then
      category="added"
      clean_msg="${BASH_REMATCH[3]}"
    elif [[ "$msg" =~ ^(fix|bugfix|patch|hotfix)(\(.*\))?!?:\ *(.+) ]]; then
      category="fixed"
      clean_msg="${BASH_REMATCH[3]}"
    elif [[ "$msg" =~ ^(chore|refactor|improve|update|perf)(\(.*\))?!?:\ *(.+) ]]; then
      category="changed"
      clean_msg="${BASH_REMATCH[3]}"
    elif [[ "$msg" =~ ^(remove|deprecate|delete|drop)(\(.*\))?!?:\ *(.+) ]]; then
      category="removed"
      clean_msg="${BASH_REMATCH[3]}"
    elif [[ "$msg" =~ ^(docs|doc|style|test|ci|build)(\(.*\))?!?:\ *(.+) ]]; then
      category="changed"
      clean_msg="${BASH_REMATCH[3]}"
    fi

    # Format commit link
    local commit_link=""
    if [[ -n "$PROJECT_URL" ]]; then
      commit_link=" ([${hash:0:7}](${PROJECT_URL}/commit/${hash}))"
    else
      commit_link=" (${hash:0:7})"
    fi

    case "$category" in
      added)   added+="${clean_msg}${commit_link}"$'\n' ;;
      fixed)   fixed+="${clean_msg}${commit_link}"$'\n' ;;
      changed) changed+="${clean_msg}${commit_link}"$'\n' ;;
      removed) removed+="${clean_msg}${commit_link}"$'\n' ;;
      other)   other+="- ${clean_msg}${commit_link}"$'\n' ;;
    esac
  done < <(git log "$range" --format="%H|%s" --no-merges 2>/dev/null)

  # 鈹€鈹€鈹€ Write sections 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
  write_section() {
    local title="$1"
    local content="$2"
    if [[ -n "$content" ]]; then
      echo "### $title" >> "$OUTPUT_FILE"
      echo "" >> "$OUTPUT_FILE"
      while IFS= read -r line; do
        [[ -n "$line" ]] && echo "- $line" >> "$OUTPUT_FILE"
      done <<< "$content"
      echo "" >> "$OUTPUT_FILE"
    fi
  }

  write_section "Added" "$added"
  write_section "Fixed" "$fixed"
  write_section "Changed" "$changed"
  write_section "Removed" "$removed"

  if [[ -n "$other" ]]; then
    echo "### Other" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "$other" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
  fi

  # 鈹€鈹€鈹€ Stats 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
  local total_commits
  total_commits=$(git log "$range" --oneline --no-merges 2>/dev/null | wc -l)
  local contributors
  contributors=$(git log "$range" --format="%an" --no-merges 2>/dev/null | sort -u | wc -l)

  echo "---" >> "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
  echo "*馃搳 $total_commits commits from $contributors contributors*" >> "$OUTPUT_FILE"
}

# 鈹€鈹€鈹€ Main 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
echo "馃攧 Generating CHANGELOG..."
>"$OUTPUT_FILE"  # Clear file
generate_changelog
echo "鉁?Done! Changelog written to: $OUTPUT_FILE"
echo ""
echo "馃搫 Preview:"
echo "鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€"
head -30 "$OUTPUT_FILE"
echo "..."
echo "鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€"
echo ""
echo "馃挕 Tip: Edit $OUTPUT_FILE and add manual entries before committing."
