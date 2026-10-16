#!/usr/bin/env bash
# ==============================================================================
# changelog.sh - Structured CHANGELOG.md generator from Git history
# Adheres to Keep a Changelog (1.1.0) and Semantic Versioning.
# Compatible with macOS default Bash 3.2+ and modern Bash 4/5.
# ==============================================================================

set -euo pipefail

# Default configuration
OUTPUT_FILE="./CHANGELOG.md"
FORCE=0
SINCE_REF=""
VERSION_NAME="Unreleased"
REPO_DIR="."

show_help() {
  cat <<'EOF'
Usage: changelog.sh [options]

Options:
  -o, --output FILE   Output file path (default: ./CHANGELOG.md). Use '-' for stdout.
  -f, --force         Overwrite output file if it already exists.
      --since REF     Starting Git reference/tag (default: latest reachable tag).
      --version NAME  Changelog section heading name (default: "Unreleased").
  -C, --repo DIR      Path to target Git repository (default: current directory).
  -h, --help          Display this help message and exit.

Exit Codes:
  0  Success
  1  Runtime error (Git execution or write failure)
  2  Usage error (invalid argument or missing value)
  3  Output file exists and --force was not specified
  4  Target is not a valid Git repository or --since ref is invalid
  5  No commits found in the specified range
EOF
}

# Parse command line arguments
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help)
      show_help
      exit 0
      ;;
    -o|--output)
      [ $# -ge 2 ] || { echo "Error: $1 requires an argument." >&2; exit 2; }
      OUTPUT_FILE="$2"
      shift 2
      ;;
    -f|--force)
      FORCE=1
      shift
      ;;
    --since)
      [ $# -ge 2 ] || { echo "Error: $1 requires an argument." >&2; exit 2; }
      SINCE_REF="$2"
      shift 2
      ;;
    --version)
      [ $# -ge 2 ] || { echo "Error: $1 requires an argument." >&2; exit 2; }
      VERSION_NAME="$2"
      shift 2
      ;;
    -C|--repo)
      [ $# -ge 2 ] || { echo "Error: $1 requires an argument." >&2; exit 2; }
      REPO_DIR="$2"
      shift 2
      ;;
    -*)
      echo "Error: Unknown option: $1" >&2
      echo "Use --help for usage instructions." >&2
      exit 2
      ;;
    *)
      echo "Error: Unexpected positional argument: $1" >&2
      exit 2
      ;;
  esac
done

# Navigate to target repo
if [ ! -d "$REPO_DIR" ]; then
  echo "Error: Directory does not exist: $REPO_DIR" >&2
  exit 4
fi

# Validate git repo
if ! git -C "$REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: Not a valid Git repository: $REPO_DIR" >&2
  exit 4
fi

# Check output file existence early (unless stdout or --force)
if [ "$OUTPUT_FILE" != "-" ] && [ -e "$OUTPUT_FILE" ] && [ "$FORCE" -ne 1 ]; then
  echo "Error: Destination file '$OUTPUT_FILE' already exists. Use --force to overwrite." >&2
  exit 3
fi

# Determine baseline since ref
if [ -z "$SINCE_REF" ]; then
  LATEST_TAG=$(git -C "$REPO_DIR" describe --tags --abbrev=0 2>/dev/null || true)
  if [ -n "$LATEST_TAG" ]; then
    SINCE_REF="$LATEST_TAG"
  fi
fi

# Determine git range
if [ -n "$SINCE_REF" ]; then
  if ! git -C "$REPO_DIR" rev-parse --verify --quiet "${SINCE_REF}^{commit}" >/dev/null 2>&1; then
    echo "Error: Reference not found or invalid: $SINCE_REF" >&2
    exit 4
  fi
  RANGE="${SINCE_REF}..HEAD"
else
  RANGE="HEAD"
fi

# Check if there are any commits in range
COMMIT_COUNT=$(git -C "$REPO_DIR" rev-list --count --no-merges "$RANGE" 2>/dev/null || echo 0)
if [ "$COMMIT_COUNT" -eq 0 ]; then
  echo "Notice: No commits found in range '${RANGE}'." >&2
  exit 5
fi

# Get GitHub repo web URL if available for clickable commit hash links
ORIGIN_URL=$(git -C "$REPO_DIR" config --get remote.origin.url 2>/dev/null || true)
REPO_WEB_URL=""
if [ -n "$ORIGIN_URL" ]; then
  CLEAN_URL=$(echo "$ORIGIN_URL" | sed -E -e 's|^git@github\.com:|https://github.com/|' -e 's|\.git$||')
  case "$CLEAN_URL" in
    https://github.com/*)
      REPO_WEB_URL="$CLEAN_URL"
      ;;
  esac
fi

# Prepare temp directory for category buckets
TMP_DIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'changelog')
trap 'rm -rf "$TMP_DIR"' EXIT

FILE_ADDED="$TMP_DIR/added.txt"
FILE_FIXED="$TMP_DIR/fixed.txt"
FILE_CHANGED="$TMP_DIR/changed.txt"
FILE_REMOVED="$TMP_DIR/removed.txt"

touch "$FILE_ADDED" "$FILE_FIXED" "$FILE_CHANGED" "$FILE_REMOVED"

# Helper to capitalize first letter (POSIX / Bash 3.2 compatible)
capitalize_first() {
  local str="$1"
  if [ -z "$str" ]; then
    echo ""
    return
  fi
  local first
  local rest
  first=$(echo "${str:0:1}" | tr '[:lower:]' '[:upper:]')
  rest="${str:1}"
  echo "${first}${rest}"
}

# Read commits separated by unit separator (0x1f)
# Format: %H (full hash), %x1f (delimiter), %s (subject)
RAW_LOG="$TMP_DIR/raw_git_log.txt"
git -C "$REPO_DIR" log "$RANGE" --no-merges --format="%H%x1f%s" > "$RAW_LOG"

while IFS="$(printf '\x1f')" read -r commit_hash subject; do
  [ -n "$commit_hash" ] || continue
  [ -n "$subject" ] || continue

  # Filter out automatic release or bump commits
  case "$subject" in
    chore\(release\)*|release:*|bump\ *|Release\ *)
      continue
      ;;
  esac

  short_hash="${commit_hash:0:7}"
  if [ -n "$REPO_WEB_URL" ]; then
    hash_link="([\`${short_hash}\`](${REPO_WEB_URL}/commit/${commit_hash}))"
  else
    hash_link="(\`${short_hash}\`)"
  fi

  is_breaking=0
  category=""
  clean_title=""

  # 1. Check for Conventional Commit pattern: type(scope)!: message OR type!: message OR type(scope): message OR type: message
  # Detect breaking change marker
  if echo "$subject" | grep -Eq '^[a-zA-Z0-9_-]+(\([^)]+\))?(!)?:[[:space:]]+'; then
    if echo "$subject" | grep -Eq '^[a-zA-Z0-9_-]+(\([^)]+\))?!:[[:space:]]+'; then
      is_breaking=1
    fi
  fi
  if echo "$subject" | grep -Eq 'BREAKING CHANGE|BREAKING:'; then
    is_breaking=1
  fi

  if echo "$subject" | grep -Eq '^[a-zA-Z0-9_-]+(\([^)]+\))?(!)?:[[:space:]]+'; then
    raw_type=$(echo "$subject" | sed -E 's/^([a-zA-Z0-9_-]+)(\([^)]+\))?(!)?:[[:space:]]+.*$/\1/' | tr '[:upper:]' '[:lower:]')
    raw_desc=$(echo "$subject" | sed -E 's/^[a-zA-Z0-9_-]+(\([^)]+\))?(!)?:[[:space:]]+//')
    clean_title=$(capitalize_first "$raw_desc")

    case "$raw_type" in
      feat)
        category="Added"
        ;;
      fix)
        category="Fixed"
        ;;
      revert|remove|removed)
        category="Removed"
        ;;
      refactor|perf|docs|style|build|ci|test|chore)
        category="Changed"
        ;;
      *)
        category="Changed"
        ;;
    esac
  else
    # 2. Keyword fallback: inspect first word
    first_word=$(echo "$subject" | awk '{print tolower($1)}' | tr -d ':,;!?')
    clean_title=$(capitalize_first "$subject")

    case "$first_word" in
      add|adds|added|introduce|introduces|introduced|new|create|creates|created|implement|implements|implemented)
        category="Added"
        ;;
      fix|fixes|fixed|resolve|resolves|resolved|patch|patches|patched|correct|corrects|corrected)
        category="Fixed"
        ;;
      remove|removes|removed|delete|deletes|deleted|drop|drops|dropped|deprecate|deprecates|deprecated)
        category="Removed"
        ;;
      *)
        category="Changed"
        ;;
    esac
  fi

  prefix=""
  if [ "$is_breaking" -eq 1 ]; then
    prefix="**BREAKING:** "
  fi

  entry="- ${prefix}${clean_title} ${hash_link}"

  case "$category" in
    Added)
      echo "$entry" >> "$FILE_ADDED"
      ;;
    Fixed)
      echo "$entry" >> "$FILE_FIXED"
      ;;
    Changed)
      echo "$entry" >> "$FILE_CHANGED"
      ;;
    Removed)
      echo "$entry" >> "$FILE_REMOVED"
      ;;
  esac

done < "$RAW_LOG"

# Generate Changelog Markdown content
TARGET_DATE=$(date -u "+%Y-%m-%d")
RENDERED_CONTENT="$TMP_DIR/rendered_changelog.md"

cat <<EOF > "$RENDERED_CONTENT"
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [${VERSION_NAME}] - ${TARGET_DATE}
EOF

# Append sections in standard order: Added, Fixed, Changed, Removed
append_section() {
  local section_name="$1"
  local section_file="$2"
  if [ -s "$section_file" ]; then
    printf '\n### %s\n\n' "$section_name" >> "$RENDERED_CONTENT"
    cat "$section_file" >> "$RENDERED_CONTENT"
  fi
}

append_section "Added" "$FILE_ADDED"
append_section "Fixed" "$FILE_FIXED"
append_section "Changed" "$FILE_CHANGED"
append_section "Removed" "$FILE_REMOVED"

printf '\n' >> "$RENDERED_CONTENT"

# Output rendering
if [ "$OUTPUT_FILE" = "-" ]; then
  cat "$RENDERED_CONTENT"
else
  # Atomic write: write to temp file next to destination then mv
  OUT_DIR=$(dirname "$OUTPUT_FILE")
  mkdir -p "$OUT_DIR"
  TMP_OUT=$(mktemp "${OUT_DIR}/.changelog_tmp.XXXXXX" 2>/dev/null || mktemp "$TMP_DIR/out.XXXXXX")
  cp "$RENDERED_CONTENT" "$TMP_OUT"
  mv "$TMP_OUT" "$OUTPUT_FILE"
  echo "Successfully generated CHANGELOG at: $OUTPUT_FILE" >&2
fi

exit 0
