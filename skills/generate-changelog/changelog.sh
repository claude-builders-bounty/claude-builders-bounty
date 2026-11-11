#!/usr/bin/env bash
# ==============================================================================
# generate-changelog: Generate structured CHANGELOG.md from git commit history
# Conforms to "Keep a Changelog" format (https://keepachangelog.com/)
# Zero external dependencies (pure Bash & git)
# ==============================================================================

set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
TARGET_TAG=""
SINCE_TAG=""
RELEASE_DATE="$(date +'%Y-%m-%d')"
DRY_RUN=false

show_help() {
  cat << 'EOF'
Usage: changelog.sh [OPTIONS]

Generate a structured CHANGELOG.md from git commit history.

Options:
  -o, --output FILE    Output file path (default: CHANGELOG.md)
  -t, --tag TAG        Release tag/version header (default: [Unreleased])
  -s, --since TAG      Generate changelog since specific tag (default: latest tag)
  -d, --dry-run        Print output to stdout without writing to file
  -h, --help           Display this help message and exit

Examples:
  bash changelog.sh
  bash changelog.sh --tag v1.0.0 --output CHANGELOG.md
  bash changelog.sh --dry-run
EOF
}

# Parse command line options
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    -t|--tag)
      TARGET_TAG="$2"
      shift 2
      ;;
    -s|--since)
      SINCE_TAG="$2"
      shift 2
      ;;
    -d|--dry-run)
      DRY_RUN=true
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      show_help
      exit 1
      ;;
  esac
done

# Verify git repository
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: current directory is not a git repository." >&2
  exit 1
fi

# Detect range of commits
if [[ -z "$SINCE_TAG" ]]; then
  LATEST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo "")"
  if [[ -n "$LATEST_TAG" ]]; then
    SINCE_TAG="$LATEST_TAG"
    RANGE="${SINCE_TAG}..HEAD"
  else
    RANGE="HEAD"
  fi
else
  RANGE="${SINCE_TAG}..HEAD"
fi

VERSION_HEADER="${TARGET_TAG:-Unreleased}"

# Temporary arrays for categorized items
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

# Read commits in chronological order for the range
while IFS= read -r commit_line || [[ -n "$commit_line" ]]; do
  [[ -z "$commit_line" ]] && continue

  # Extract hash and subject (format: %h %s)
  hash="${commit_line%% *}"
  subject="${commit_line#* }"

  # Ignore merge commits
  if [[ "$subject" =~ ^Merge ]]; then
    continue
  fi

  # Categorize commit by conventional prefix or intent
  lower_subject="$(echo "$subject" | tr '[:upper:]' '[:lower:]')"

  re_added='^(feat|feature|add|new|implement)(\([^)]*\))?:[[:space:]]+(.*)$'
  re_fixed='^(fix|bug|patch|hotfix|resolve)(\([^)]*\))?:[[:space:]]+(.*)$'
  re_removed='^(remove|delete|deprecate|drop)(\([^)]*\))?:[[:space:]]+(.*)$'
  re_changed='^(refactor|perf|change|update|docs|style|chore|ci|test|build)(\([^)]*\))?:[[:space:]]+(.*)$'

  if [[ "$lower_subject" =~ $re_added ]]; then
    clean_msg="${subject#*: }"
    ADDED+=("- ${clean_msg} ([${hash}](${hash}))")
  elif [[ "$lower_subject" =~ $re_fixed ]]; then
    clean_msg="${subject#*: }"
    FIXED+=("- ${clean_msg} ([${hash}](${hash}))")
  elif [[ "$lower_subject" =~ $re_removed ]]; then
    clean_msg="${subject#*: }"
    REMOVED+=("- ${clean_msg} ([${hash}](${hash}))")
  elif [[ "$lower_subject" =~ $re_changed ]]; then
    clean_msg="${subject#*: }"
    CHANGED+=("- ${clean_msg} ([${hash}](${hash}))")
  else
    # Fallback keyword checks
    if [[ "$lower_subject" =~ (^|[[:space:]])(add|new|feature)($|[[:space:]]) ]]; then
      ADDED+=("- ${subject} ([${hash}](${hash}))")
    elif [[ "$lower_subject" =~ (^|[[:space:]])(fix|bug|issue|resolve)($|[[:space:]]) ]]; then
      FIXED+=("- ${subject} ([${hash}](${hash}))")
    elif [[ "$lower_subject" =~ (^|[[:space:]])(remove|deprecat|delete)($|[[:space:]]) ]]; then
      REMOVED+=("- ${subject} ([${hash}](${hash}))")
    else
      CHANGED+=("- ${subject} ([${hash}](${hash}))")
    fi
  fi
done < <(git log "${RANGE}" --no-merges --format="%h %s" --reverse 2>/dev/null || true)

# Build changelog section
CHANGELOG_ENTRY=""
CHANGELOG_ENTRY+="## [${VERSION_HEADER}] - ${RELEASE_DATE}"$'\n\n'

has_content=false

if [[ ${#ADDED[@]} -gt 0 ]]; then
  has_content=true
  CHANGELOG_ENTRY+="### Added"$'\n'
  for item in "${ADDED[@]}"; do
    CHANGELOG_ENTRY+="${item}"$'\n'
  done
  CHANGELOG_ENTRY+=$'\n'
fi

if [[ ${#FIXED[@]} -gt 0 ]]; then
  has_content=true
  CHANGELOG_ENTRY+="### Fixed"$'\n'
  for item in "${FIXED[@]}"; do
    CHANGELOG_ENTRY+="${item}"$'\n'
  done
  CHANGELOG_ENTRY+=$'\n'
fi

if [[ ${#CHANGED[@]} -gt 0 ]]; then
  has_content=true
  CHANGELOG_ENTRY+="### Changed"$'\n'
  for item in "${CHANGED[@]}"; do
    CHANGELOG_ENTRY+="${item}"$'\n'
  done
  CHANGELOG_ENTRY+=$'\n'
fi

if [[ ${#REMOVED[@]} -gt 0 ]]; then
  has_content=true
  CHANGELOG_ENTRY+="### Removed"$'\n'
  for item in "${REMOVED[@]}"; do
    CHANGELOG_ENTRY+="${item}"$'\n'
  done
  CHANGELOG_ENTRY+=$'\n'
fi

if [[ "$has_content" == false ]]; then
  CHANGELOG_ENTRY+="*No significant changes found in range ${RANGE}.*"$'\n\n'
fi

if [[ "$DRY_RUN" == true ]]; then
  echo "$CHANGELOG_ENTRY"
  exit 0
fi

# Write or prepend to CHANGELOG.md
HEADER="# Changelog"$'\n\n'"All notable changes to this project will be documented in this file."$'\n\n'"The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)."$'\n\n'

if [[ ! -f "$OUTPUT_FILE" ]]; then
  printf "%s%s" "$HEADER" "$CHANGELOG_ENTRY" > "$OUTPUT_FILE"
  echo "Created ${OUTPUT_FILE} with ${VERSION_HEADER} release entries."
else
  # Prepend new version under the main header
  existing_content="$(cat "$OUTPUT_FILE")"
  if [[ "$existing_content" =~ ^#\ Changelog ]]; then
    # Strip existing header and prepend new entry right below header
    rest_content="$(echo "$existing_content" | sed '1,4d')"
    printf "%s%s\n%s" "$HEADER" "$CHANGELOG_ENTRY" "$rest_content" > "$OUTPUT_FILE"
  else
    printf "%s%s\n%s" "$HEADER" "$CHANGELOG_ENTRY" "$existing_content" > "$OUTPUT_FILE"
  fi
  echo "Updated ${OUTPUT_FILE} with ${VERSION_HEADER} release entries."
fi
