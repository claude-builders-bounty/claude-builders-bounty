#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# generate-changelog.sh
#
# Generate a structured CHANGELOG.md from conventional commits in git history.
#
# Parses commits matching the Conventional Commits specification:
#   type(scope)!: description
#
# Groups by version (git tags) or date ranges, and outputs a formatted
# CHANGELOG.md with emoji-labelled sections.
#
# Usage:
#   ./generate-changelog.sh [--from <tag>] [--to <tag>] [--output <file>] [--group-by <type|scope>]
#
# Options:
#   --from <tag>       Start tag (inclusive). Default: first tag reachable from HEAD.
#   --to <tag>         End tag (inclusive). Default: HEAD.
#   --output <file>    Output file path. Default: CHANGELOG.md
#   --group-by <type|scope>  Group commits by 'type' (default) or 'scope'.
#   --help             Show this help message.
# =============================================================================

# ---- Color & Emoji Setup ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Emoji and label lookup (bash 3.2 compatible — no associative arrays)
get_type_info() {
  local type="$1"
  case "$type" in
    feat)     echo "✨|Features" ;;
    fix)      echo "🐛|Bug Fixes" ;;
    docs)     echo "📝|Documentation" ;;
    chore)    echo "🧹|Chores" ;;
    refactor) echo "♻️|Refactors" ;;
    test)     echo "🧪|Tests" ;;
    perf)     echo "⚡|Performance" ;;
    style)    echo "🎨|Style" ;;
    *)        echo "❓|Other" ;;
  esac
}

# ---- Defaults ----
FROM_TAG=""
TO_TAG="HEAD"
OUTPUT_FILE="CHANGELOG.md"
GROUP_BY="type"

# ---- Help ----
show_help() {
  cat <<EOF
Usage: $(basename "$0") [options]

Generate a structured CHANGELOG.md from conventional commits in git history.

Options:
  --from <tag>       Start tag (inclusive). Default: first tag reachable from HEAD.
  --to <tag>         End tag (inclusive). Default: HEAD.
  --output <file>    Output file path. Default: CHANGELOG.md
  --group-by <type|scope>  Group commits by 'type' (default) or 'scope'.
  --help             Show this help message and exit.
EOF
  exit 0
}

# ---- Parse Arguments ----
while [[ $# -gt 0 ]]; do
  case "$1" in
    --from)    FROM_TAG="$2"; shift 2 ;;
    --to)      TO_TAG="$2";   shift 2 ;;
    --output)  OUTPUT_FILE="$2"; shift 2 ;;
    --group-by) GROUP_BY="$2"; shift 2 ;;
    --help)    show_help ;;
    *)         printf "${RED}Unknown option: $1${NC}\n" >&2; show_help ;;
  esac
done

if ! git rev-parse --git-dir > /dev/null 2>&1; then
  printf "${RED}Error: Not a git repository.${NC}\n" >&2
  exit 1
fi

if [[ "$GROUP_BY" != "type" && "$GROUP_BY" != "scope" ]]; then
  printf "${RED}Error: --group-by must be 'type' or 'scope'.${NC}\n" >&2
  exit 1
fi

# ---- Resolve tag range ----
resolve_range() {
  local from="$1"
  local to="$2"

  # If no --from given, find the first tag reachable from HEAD
  if [[ -z "$from" ]]; then
    from=$(git tag --merged HEAD 2>/dev/null | sort -V | head -1 || true)
    if [[ -z "$from" ]]; then
      from=""
    fi
  fi

  # Validate --from tag
  if [[ -n "$from" ]] && ! git rev-parse --verify "$from" >/dev/null 2>&1; then
    printf "${RED}Error: Tag '$from' not found.${NC}\n" >&2
    exit 1
  fi

  # Validate --to tag (if not HEAD)
  if [[ "$to" != "HEAD" ]] && ! git rev-parse --verify "$to" >/dev/null 2>&1; then
    printf "${RED}Error: Tag '$to' not found.${NC}\n" >&2
    exit 1
  fi

  echo "$from|$to"
}

# ---- Parse conventional commits ----
parse_commits() {
  local from="$1"
  local to="$2"
  local range

  if [[ -z "$from" ]]; then
    range="$to"
  else
    range="${from}..${to}"
  fi

  # Format: <hash>|<type>|<scope>|<description>|<date>
  git log --reverse --no-merges --format="%H|%s|%ai" "$range" 2>/dev/null | \
    while IFS='|' read -r hash subject date; do
      # Parse conventional commit: type(scope)!: description
      local re='^([a-zA-Z]+)(\(([^)]*)\))?(!)?: (.+)$'
      if [[ "$subject" =~ $re ]]; then
        type="${BASH_REMATCH[1]}"
        scope="${BASH_REMATCH[3]:-}"
        breaking="${BASH_REMATCH[4]}"
        desc="${BASH_REMATCH[5]}"
        echo "${type}|${scope}|${desc}|${date}|${hash}|${breaking}"
      fi
    done
}

# ---- Group commits by version tags ----
group_by_version() {
  local from="$1"
  local to="$2"
  local group_by="$3"

  # Collect all tags in range, sorted semantically
  local tags=()
  while IFS= read -r tag; do
    tags+=("$tag")
  done < <(git tag --merged HEAD 2>/dev/null | sort -V || true)

  local output=""
  local prev_tag=""

  if [[ ${#tags[@]} -eq 0 ]]; then
    # No tags — treat entire history as one version
    local block
    block=$(generate_version_block "" "$to" "$GROUP_BY" "")
    block="${block%.}"
    output="$block"
    # Determine which tags fall in our range
    local in_range_tags=()
    local start_found=false
    local stop_found=false

    for tag in "${tags[@]}"; do
      if [[ -z "$FROM_TAG" ]] || [[ "$tag" == "$FROM_TAG" ]]; then
        start_found=true
      fi
      if $start_found; then
        in_range_tags+=("$tag")
      fi
      if [[ "$tag" == "$TO_TAG" ]]; then
        stop_found=true
        break
      fi
    done

    # If --to is HEAD (not a tag), include all tags up to HEAD
    if [[ "$TO_TAG" == "HEAD" ]]; then
      stop_found=true
    fi

    # Generate blocks for each tag range
    local prev=""
    for tag in "${in_range_tags[@]}"; do
      if [[ -z "$prev" ]]; then
        block=$(generate_version_block "" "$tag" "$GROUP_BY" "$tag")
      else
        block=$(generate_version_block "$prev" "$tag" "$GROUP_BY" "$tag")
      fi
      block="${block%.}"
      [[ -n "$block" ]] && output+="${block}"$'\n\n'
      prev="$tag"
    done

    # Remaining commits after last tag up to HEAD
    if [[ "$TO_TAG" == "HEAD" ]] && [[ "${#in_range_tags[@]}" -gt 0 ]]; then
      local last_tag="${in_range_tags[${#in_range_tags[@]}-1]}"
      block=$(generate_version_block "$last_tag" "HEAD" "$GROUP_BY" "Unreleased")
      block="${block%.}"
      [[ -n "$block" ]] && output+="${block}"$'\n\n'
    fi
  fi

  echo "$output"
}

# ---- Generate a version block ----
generate_version_block() {
  local from="$1"
  local to="$2"
  local group_by="$3"
  local version_label="$4"
  local commits

  commits=$(parse_commits "$from" "$to")

  if [[ -z "$commits" ]]; then
    return
  fi

  local version_header
  if [[ -z "$version_label" ]]; then
    version_label="Unreleased"
  fi
  version_header="## [${version_label}]"

  # Add date if we have a tag
  local tag_date=""
  if git rev-parse --verify "$version_label" >/dev/null 2>&1; then
    tag_date=$(git log -1 --format="%ai" "$version_label" 2>/dev/null | cut -d' ' -f1 || true)
  fi
  if [[ -n "$tag_date" ]]; then
    version_header="${version_header} - ${tag_date}"
  fi

  local block=""
  block+="${version_header}\n\n"

  if [[ "$group_by" == "scope" ]]; then
    # Group by scope
    local scopes
    scopes=$(echo "$commits" | awk -F'|' '{print $2}' | sort -u)
    while IFS= read -r scope; do
      [[ -z "$scope" ]] && scope="general"
      block+="### ${scope}\n\n"
      while IFS='|' read -r type sc desc date hash breaking; do
        local prefix=""
        [[ -n "$breaking" ]] && prefix="**BREAKING:** "
        block+="  - ${prefix}${desc} ([${hash:0:7}](${hash}))\n"
      done < <(echo "$commits" | awk -F'|' -v s="$scope" '$2 == s || (s == "general" && $2 == "")')
      block+="\n"
    done
  else
    # Group by type
    local ordered_types=("feat" "fix" "docs" "refactor" "perf" "test" "chore" "style")
    for type in "${ordered_types[@]}"; do
      local type_commits
      type_commits=$(echo "$commits" | awk -F'|' -v t="$type" '$1 == t')
      if [[ -n "$type_commits" ]]; then
        local info
        info=$(get_type_info "$type")
        local emoji="${info%%|*}"
        local label="${info#*|}"
        block+="### ${emoji} ${label}\n\n"
        while IFS='|' read -r t sc desc date hash breaking; do
          local prefix=""
          [[ -n "$breaking" ]] && prefix="**BREAKING:** "
          local scope_str=""
          [[ -n "$sc" ]] && scope_str=" (\`${sc}\`)"
          block+="  - ${prefix}${desc}${scope_str} ([${hash:0:7}](${hash}))\n"
        done < <(echo "$commits" | awk -F'|' -v t="$type" '$1 == t')
        block+="\n"
      fi
    done
  fi

  printf "%b\n." "$block"
}

# ---- Main ----
main() {
  printf "${BOLD}${BLUE}Generating CHANGELOG...${NC}\n"

  # Resolve tag range
  IFS='|' read -r resolved_from resolved_to < <(resolve_range "$FROM_TAG" "$TO_TAG")
  FROM_TAG="$resolved_from"
  TO_TAG="$resolved_to"

  printf "  ${CYAN}Range:${NC} ${FROM_TAG:-<beginning>} → ${TO_TAG}\n"
  printf "  ${CYAN}Group by:${NC} ${GROUP_BY}\n"
  printf "  ${CYAN}Output:${NC} ${OUTPUT_FILE}\n"
  printf "\n"

  # Generate changelog content
  local changelog
  changelog=$(group_by_version "$FROM_TAG" "$TO_TAG" "$GROUP_BY")

  # Prepend header
  local header="# Changelog\n\n"
  header+="All notable changes to this project will be documented in this file.\n"
  header+="This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)\n"
  header+="and follows [Conventional Commits](https://www.conventionalcommits.org/).\n\n"

  local full_content="${header}${changelog}"

  # If output file exists, prepend new content
  if [[ -f "$OUTPUT_FILE" ]]; then
    local existing
    existing=$(cat "$OUTPUT_FILE")
    # Remove old header (lines starting with #) to avoid duplication
    existing=$(echo "$existing" | sed -n '/^## /,$ p')
    full_content="${header}${changelog}\n${existing}"
  fi

  printf "%b" "$full_content" > "$OUTPUT_FILE"
  printf "${GREEN}${BOLD}✓ CHANGELOG generated: ${OUTPUT_FILE}${NC}\n"
}

main "$@"
