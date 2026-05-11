#!/usr/bin/env bash
# generate-changelog — structured CHANGELOG.md from git history
# Usage: ./changelog.sh [output_file]
#
# Auto-categorizes commits since the last git tag into:
#   Added, Fixed, Changed, Removed
#
# Commit prefix convention (conventional commits friendly):
#   feat:  → Added
#   fix:   → Fixed
#   refactor|perf|style|chore|deps|deps-dev: → Changed
#   remove|delete|drop|removal: → Removed
#   BREAKING CHANGE: → Changed (with breaking marker)
#
# Assisted-by: Claude (Anthropic)

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_URL="${2:-$(git remote get-url origin 2>/dev/null || echo '')}"

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

last_tag() {
  git describe --tags --abbrev=0 2>/dev/null || echo ""
}

commit_range() {
  local tag="$1"
  if [[ -n "$tag" ]]; then
    echo "${tag}..HEAD"
  else
    echo "HEAD"
  fi
}

# Map commit subject to category
 categorize() {
  local msg="$1"
  local lower="$(echo "$msg" | tr '[:upper:]' '[:lower:]')"

  # Breaking changes always go to Changed
  if [[ "$lower" == *"breaking change"* ]] || [[ "$msg" == *"!:"* ]]; then
    echo "Changed"
    return
  fi

  # Extract prefix before colon
  local prefix=""
  if [[ "$msg" =~ ^([a-zA-Z0-9_-]+)(\(.+\))?!?: ]]; then
    prefix="${BASH_REMATCH[1]}"
    prefix="$(echo "$prefix" | tr '[:upper:]' '[:lower:]')"
  fi

  case "$prefix" in
    feat|feature|add|new|introduce|implement|create|support)
      echo "Added" ;;
    fix|bugfix|hotfix|patch|repair|resolve|correct)
      echo "Fixed" ;;
    remove|delete|drop|removal|deprecate|deprecation|clean|cleanup|remove*)
      echo "Removed" ;;
    refactor|perf|performance|style|chore|deps|deps-dev|update|upgrade|downgrade|ci|build|test|docs|doc|security|bump|migrate|rework|improve|enhance|polish|tweak|adjust|optimize|consolidate|reorganize|restructure|rewrite)
      echo "Changed" ;;
    *)
      # Fallback heuristics
      if [[ "$lower" == "add "* ]] || [[ "$lower" == "introduce "* ]] || [[ "$lower" == "implement "* ]] || [[ "$lower" == "create "* ]] || [[ "$lower" == "support "* ]]; then
        echo "Added"
      elif [[ "$lower" == "fix "* ]] || [[ "$lower" == "resolve "* ]] || [[ "$lower" == "correct "* ]] || [[ "$lower" == "repair "* ]] || [[ "$lower" == "patch "* ]]; then
        echo "Fixed"
      elif [[ "$lower" == "remove "* ]] || [[ "$lower" == "delete "* ]] || [[ "$lower" == "drop "* ]] || [[ "$lower" == "clean "* ]] || [[ "$lower" == "deprecate "* ]]; then
        echo "Removed"
      else
        echo "Changed"
      fi
      ;;
  esac
}

# Extract clean message (strip prefix)
clean_msg() {
  local msg="$1"
  # Strip conventional commit prefix
  msg="$(echo "$msg" | sed -E 's/^[a-zA-Z0-9_-]+(\([^)]+\))?!?: *//')"
  # Strip leading/trailing whitespace
  msg="$(echo "$msg" | sed -E 's/^[[:space:]]+//;s/[[:space:]]+$//')"
  echo "$msg"
}

# Get short SHA
commit_sha() {
  git log -1 --format="%h" "$1"
}

# Get commit date
commit_date() {
  git log -1 --format="%Y-%m-%d" "$1"
}

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

main() {
  if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "Error: not a git repository" >&2
    exit 1
  fi

  local tag
  tag=$(last_tag)

  local range
  range=$(commit_range "$tag")

  local version_label
  if [[ -n "$tag" ]]; then
    version_label="## [Unreleased] — since ${tag}"
  else
    version_label="## [Unreleased]"
  fi

  # Collect commits
  local added=()
  local fixed=()
  local changed=()
  local removed=()

  while IFS= read -r line; do
    # line format: <sha> <subject>
    local sha="${line%% *}"
    local subject="${line#* }"

    [[ -z "$subject" ]] && continue

    local cat
    cat=$(categorize "$subject")
    local clean
    clean=$(clean_msg "$subject")

    # Build markdown link if repo URL available
    local entry
    if [[ -n "$REPO_URL" ]]; then
      # Normalize GitHub SSH → HTTPS
      local url="$REPO_URL"
      url="${url#git@github.com:}"
      url="${url#https://github.com/}"
      url="${url%.git}"
      entry="- ${clean} ([${sha}](https://github.com/${url}/commit/${sha}))"
    else
      entry="- ${clean} (${sha})"
    fi

    case "$cat" in
      Added)   added+=("$entry") ;;
      Fixed)   fixed+=("$entry") ;;
      Changed) changed+=("$entry") ;;
      Removed) removed+=("$entry") ;;
    esac
  done < <(git log "$range" --format="%H %s" --reverse)

  # Generate output
  {
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project are documented in this file."
    echo "Generated automatically from git history."
    echo ""
    echo "$version_label"
    echo ""

    if [[ ${#added[@]} -gt 0 ]]; then
      echo "### Added"
      printf '%s\n' "${added[@]}"
      echo ""
    fi

    if [[ ${#fixed[@]} -gt 0 ]]; then
      echo "### Fixed"
      printf '%s\n' "${fixed[@]}"
      echo ""
    fi

    if [[ ${#changed[@]} -gt 0 ]]; then
      echo "### Changed"
      printf '%s\n' "${changed[@]}"
      echo ""
    fi

    if [[ ${#removed[@]} -gt 0 ]]; then
      echo "### Removed"
      printf '%s\n' "${removed[@]}"
      echo ""
    fi

    if [[ ${#added[@]} -eq 0 && ${#fixed[@]} -eq 0 && ${#changed[@]} -eq 0 && ${#removed[@]} -eq 0 ]]; then
      echo "_No changes since last tag._"
      echo ""
    fi

    echo "---"
    echo ""
    echo "*Generated by [generate-changelog](https://github.com/claude-builders-bounty/claude-builders-bounty)*"
  } > "$OUTPUT_FILE"

  echo "✅  CHANGELOG written to: $OUTPUT_FILE"
  echo "    Commits since last tag: $((${#added[@]} + ${#fixed[@]} + ${#changed[@]} + ${#removed[@]}))"
  echo "    Added: ${#added[@]} | Fixed: ${#fixed[@]} | Changed: ${#changed[@]} | Removed: ${#removed[@]}"
}

main "$@"
