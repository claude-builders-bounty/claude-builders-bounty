#!/usr/bin/env bash
# ============================================================================
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage:
#   bash changelog.sh              # Generate CHANGELOG.md from last tag
#   bash changelog.sh --since v1.0 # Generate from a specific tag
#   bash changelog.sh --full       # Full history (no tag filter)
#   bash changelog.sh --stdout     # Print to stdout instead of file
#
# Dependencies: git, bash 4+
# Zero npm/pip/other deps required.
# ============================================================================

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────
OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""
MODE="file"  # or "stdout"
USE_FULL_HISTORY=false

# ── Parse arguments ────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE_TAG="$2"; shift 2 ;;
    --full) USE_FULL_HISTORY=true; shift ;;
    --stdout) MODE="stdout"; shift ;;
    --help|-h)
      echo "Usage: bash changelog.sh [options]"
      echo "  --since TAG   Start from specific tag"
      echo "  --full        Include full git history"
      echo "  --stdout      Print to stdout instead of CHANGELOG.md"
      echo "  --help        Show this help"
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ── Detect the tag range ───────────────────────────────────────────────────
get_tag_range() {
  if $USE_FULL_HISTORY; then
    echo ""
    return
  fi

  if [[ -n "$SINCE_TAG" ]]; then
    echo "$SINCE_TAG"
    return
  fi

  # Find the most recent tag that looks like a version (semver or date-based)
  local tags
  tags=$(git tag --sort=-creatordate 2>/dev/null | head -20)

  if [[ -z "$tags" ]]; then
    # No tags at all — use full history
    echo ""
    return
  fi

  # Pick the first (most recent) tag
  echo "$tags" | head -1
}

# ── Categorize a commit message ────────────────────────────────────────────
# Follows the Conventional Commits spec: https://www.conventionalcommits.org/
categorize() {
  local msg="$1"

  # Strip merge commits
  if echo "$msg" | grep -qiE '^Merge '; then
    echo "SKIP"
    return
  fi

  # Strip version bump / chore commits
  if echo "$msg" | grep -qiE '^(chore|release|version)(\(|:)' && \
     echo "$msg" | grep -qiE 'v?[0-9]+\.[0-9]+\.[0-9]'; then
    echo "SKIP"
    return
  fi

  # Conventional commit types → changelog sections
  local type
  type=$(echo "$msg" | grep -oE '^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert|deprecate|security|breaking)(\([^)]*\))?!?(\s+|\s*:)' | head -1)

  case "$type" in
    feat*)      echo "Added" ;;
    fix*)       echo "Fixed" ;;
    deprecate*) echo "Deprecated" ;;
    breaking*)  echo "Changed" ;;
    refactor*)  echo "Changed" ;;
    perf*)      echo "Changed" ;;
    style*)     echo "Changed" ;;
    docs*)      echo "Documentation" ;;
    test*)      echo "Changed" ;;
    build*)     echo "Changed" ;;
    ci*)        echo "Changed" ;;
    revert*)    echo "Fixed" ;;
    security*)  echo "Security" ;;
    chore*)     echo "SKIP" ;;
    *)
      # Keyword-based fallback for non-conventional messages
      if echo "$msg" | grep -qiE '^\s*(add|new|create|implement|introduce)\b'; then
        echo "Added"
      elif echo "$msg" | grep -qiE '^\s*(fix|correct|resolve|patch|hotfix|bug)\b'; then
        echo "Fixed"
      elif echo "$msg" | grep -qiE '^\s*(remove|delete|drop|deprecate)\b'; then
        echo "Removed"
      elif echo "$msg" | grep -qiE '^\s*(change|update|upgrade|bump|migrate|redesign|rewrite)\b'; then
        echo "Changed"
      elif echo "$msg" | grep -qiE '^\s*(doc|document|comment)\b'; then
        echo "Documentation"
      elif echo "$msg" | grep -qiE '^\s*(security|vulnerability|audit|CVE)\b'; then
        echo "Security"
      else
        echo "Changed"  # Default bucket
      fi
      ;;
  esac
}

# ── Format a commit line ───────────────────────────────────────────────────
format_commit() {
  local msg="$1"
  local hash="$2"

  # Clean up the message: remove the type prefix for readability
  local cleaned
  cleaned=$(echo "$msg" | sed -E 's/^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert|deprecate|security|breaking|remove)(\([^)]*\))?!?:\s*//' | sed -E 's/^[[:space:]]*//')

  # Capitalize first letter
  cleaned="$(echo "${cleaned:0:1}" | tr '[:lower:]' '[:upper:]')${cleaned:1}"

  # Extract scope if present
  local scope=""
  scope=$(echo "$msg" | grep -oE '^[a-z]+\(([^)]+)\)' | grep -oE '\([^)]+\)' | tr -d '()')

  if [[ -n "$scope" ]]; then
    echo "- **${scope}:** ${cleaned} ([${hash:0:7}](https://github.com/REPO_OWNER/REPO_NAME/commit/${hash}))"
  else
    echo "- ${cleaned} ([${hash:0:7}](https://github.com/REPO_OWNER/REPO_NAME/commit/${hash}))"
  fi
}

# ── Get repo info for URLs ─────────────────────────────────────────────────
get_repo_info() {
  local remote
  remote=$(git config --get remote.origin.url 2>/dev/null || echo "")
  if echo "$remote" | grep -qE 'github\.com[:/]'; then
    echo "$remote" | sed -E 's|.*github\.com[:/]([^/]+/[^.]+).*|\1|'
  else
    echo "owner/repo"
  fi
}

# ── Main ───────────────────────────────────────────────────────────────────
main() {
  # Verify we're in a git repo
  if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a git repository."
    exit 1
  fi

  local since_tag
  since_tag=$(get_tag_range)

  local repo_info
  repo_info=$(get_repo_info)

  # Build the git log command
  local log_cmd=("git" "log" "--pretty=format:%s|||%H" "--no-merges")

  if [[ -n "$since_tag" ]]; then
    log_cmd+=("${since_tag}..HEAD")
  fi

  # Get the commits
  local commits
  commits=$("${log_cmd[@]}" 2>/dev/null) || {
    echo "Error: Failed to get git log. Try --full if tag issues."
    exit 1
  }

  if [[ -z "$commits" ]]; then
    echo "No new commits since last tag${since_tag:+ (${since_tag})}."
    echo "Nothing to generate."
    exit 0
  fi

  # Categorize commits - initialize lists
  local added_list="" fixed_list="" changed_list="" deprecated_list=""
  local removed_list="" security_list="" docs_list=""

  local date_line
  date_line=$(date +"%Y-%m-%d")

  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    local msg="${line%%|||*}"
    local hash="${line##*|||}"

    local category
    category=$(categorize "$msg")

    [[ "$category" == "SKIP" ]] && continue

    local formatted
    formatted=$(REPO_OWNER=$(echo "$repo_info" | cut -d/ -f1) \
                REPO_NAME=$(echo "$repo_info" | cut -d/ -f2) \
                format_commit "$msg" "$hash")

    case "$category" in
      Added)         added_list="${added_list}${formatted}\n" ;;
      Fixed)         fixed_list="${fixed_list}${formatted}\n" ;;
      Changed)       changed_list="${changed_list}${formatted}\n" ;;
      Deprecated)    deprecated_list="${deprecated_list}${formatted}\n" ;;
      Removed)       removed_list="${removed_list}${formatted}\n" ;;
      Security)      security_list="${security_list}${formatted}\n" ;;
      Documentation) docs_list="${docs_list}${formatted}\n" ;;
    esac
  done <<< "$commits"

  # Determine version header
  local version_header=""
  local latest_tag
  latest_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

  if [[ -n "$latest_tag" ]]; then
    # Check if the latest tag points to HEAD
    local tag_commit head_commit
    tag_commit=$(git rev-list -n 1 "$latest_tag" 2>/dev/null || echo "")
    head_commit=$(git rev-parse HEAD 2>/dev/null || echo "")

    if [[ "$tag_commit" == "$head_commit" ]]; then
      version_header="## [${latest_tag}] - ${date_line}"
    else
      version_header="## [Unreleased]${latest_tag:+ (since ${latest_tag})} - ${date_line}"
    fi
  else
    version_header="## [Unreleased] - ${date_line}"
  fi

  # Build the changelog content
  local output=""
  output+="# Changelog\n\n"
  output+="> Auto-generated from git history. Follows [Keep a Changelog](https://keepachangelog.com/) format.\n\n"
  output+="${version_header}\n\n"

  local has_content=false

  if [[ -n "$added_list" ]]; then
    output+="### Added\n\n${added_list}\n"
    has_content=true
  fi
  if [[ -n "$fixed_list" ]]; then
    output+="### Fixed\n\n${fixed_list}\n"
    has_content=true
  fi
  if [[ -n "$changed_list" ]]; then
    output+="### Changed\n\n${changed_list}\n"
    has_content=true
  fi
  if [[ -n "$deprecated_list" ]]; then
    output+="### Deprecated\n\n${deprecated_list}\n"
    has_content=true
  fi
  if [[ -n "$removed_list" ]]; then
    output+="### Removed\n\n${removed_list}\n"
    has_content=true
  fi
  if [[ -n "$security_list" ]]; then
    output+="### Security\n\n${security_list}\n"
    has_content=true
  fi
  if [[ -n "$docs_list" ]]; then
    output+="### Documentation\n\n${docs_list}\n"
    has_content=true
  fi

  if ! $has_content; then
    output+="_No significant changes in this release._\n"
  fi

  # Write output
  if [[ "$MODE" == "stdout" ]]; then
    echo -e "$output"
  else
    echo -e "$output" > "$OUTPUT_FILE"
    echo "✅ Generated $OUTPUT_FILE"
    echo "   $(echo -e "$commits" | wc -l | tr -d ' ') commits processed"
  fi
}

main "$@"
