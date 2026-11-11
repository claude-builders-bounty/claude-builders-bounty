#!/usr/bin/env bash
#
# changelog.sh - Automatically generate structured CHANGELOG.md from git history.
# Conforms to Keep a Changelog (1.1.0) and Conventional Commits specifications.
#
set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
TARGET_TAG=""
DRY_RUN=false
SINCE_ALL=false

print_usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  -o, --output FILE    Output changelog file (default: CHANGELOG.md)
  -t, --tag TAG        Generate changelog for a specific tag
  -a, --all            Include all commits from initial commit
  -d, --dry-run        Print changelog to stdout without writing file
  -h, --help           Show this help message
EOF
    exit 0
}

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
        -a|--all)
            SINCE_ALL=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            print_usage
            ;;
        *)
            echo "Unknown option: $1" >&2
            print_usage
            ;;
    esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: current directory is not a git repository." >&2
    exit 1
fi

# Determine commit range
LAST_TAG=""
if [[ -n "$TARGET_TAG" ]]; then
    LAST_TAG="$TARGET_TAG"
elif [[ "$SINCE_ALL" = false ]]; then
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
fi

if [[ -n "$LAST_TAG" ]]; then
    COMMIT_RANGE="${LAST_TAG}..HEAD"
    TAG_INFO="since ${LAST_TAG}"
else
    COMMIT_RANGE="HEAD"
    TAG_INFO="full repository history"
fi

TODAY=$(date -u +"%Y-%m-%d")

# Temporary files for categorized commits
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

ADDED_FILE="$TMP_DIR/added.txt"
FIXED_FILE="$TMP_DIR/fixed.txt"
CHANGED_FILE="$TMP_DIR/changed.txt"
REMOVED_FILE="$TMP_DIR/removed.txt"

touch "$ADDED_FILE" "$FIXED_FILE" "$CHANGED_FILE" "$REMOVED_FILE"

# Format: %h|%s|%an
while IFS='|' read -r hash subject author; do
    [[ -z "$hash" ]] && continue
    
    # Strip conventional commit prefix for clean display
    CLEAN_MSG="$subject"
    LOWER_SUBJ=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
    
    ENTRY="- ${subject} ([${hash}](${hash}))"

    if [[ "$LOWER_SUBJ" =~ ^feat(\(.*\))?: ]]; then
        echo "$ENTRY" >> "$ADDED_FILE"
    elif [[ "$LOWER_SUBJ" =~ ^fix(\(.*\))?: ]] || [[ "$LOWER_SUBJ" =~ ^bugfix(\(.*\))?: ]]; then
        echo "$ENTRY" >> "$FIXED_FILE"
    elif [[ "$LOWER_SUBJ" =~ ^(remove|del|deprecat)(\(.*\))?: ]]; then
        echo "$ENTRY" >> "$REMOVED_FILE"
    elif [[ "$LOWER_SUBJ" =~ ^(chore|refactor|perf|docs|style|test|build|ci)(\(.*\))?: ]]; then
        echo "$ENTRY" >> "$CHANGED_FILE"
    elif [[ "$LOWER_SUBJ" =~ add|feature|new ]]; then
        echo "$ENTRY" >> "$ADDED_FILE"
    elif [[ "$LOWER_SUBJ" =~ fix|resolve|close ]]; then
        echo "$ENTRY" >> "$FIXED_FILE"
    elif [[ "$LOWER_SUBJ" =~ remove|delete|deprecate ]]; then
        echo "$ENTRY" >> "$REMOVED_FILE"
    else
        echo "$ENTRY" >> "$CHANGED_FILE"
    fi
done < <(git log "$COMMIT_RANGE" --no-merges --pretty=format:"%h|%s|%an")

# Assemble Keep a Changelog markdown
CHANGELOG_CONTENT=""
CHANGELOG_CONTENT+="# Changelog\n\n"
CHANGELOG_CONTENT+="All notable changes to this project will be documented in this file.\n\n"
CHANGELOG_CONTENT+="The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),\n"
CHANGELOG_CONTENT+="and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"
CHANGELOG_CONTENT+="## [Unreleased] - ${TODAY} (${TAG_INFO})\n\n"

has_entries=false

if [[ -s "$ADDED_FILE" ]]; then
    CHANGELOG_CONTENT+="### Added\n\n"
    CHANGELOG_CONTENT+="$(cat "$ADDED_FILE")\n\n"
    has_entries=true
fi

if [[ -s "$FIXED_FILE" ]]; then
    CHANGELOG_CONTENT+="### Fixed\n\n"
    CHANGELOG_CONTENT+="$(cat "$FIXED_FILE")\n\n"
    has_entries=true
fi

if [[ -s "$CHANGED_FILE" ]]; then
    CHANGELOG_CONTENT+="### Changed\n\n"
    CHANGELOG_CONTENT+="$(cat "$CHANGED_FILE")\n\n"
    has_entries=true
fi

if [[ -s "$REMOVED_FILE" ]]; then
    CHANGELOG_CONTENT+="### Removed\n\n"
    CHANGELOG_CONTENT+="$(cat "$REMOVED_FILE")\n\n"
    has_entries=true
fi

if [[ "$has_entries" = false ]]; then
    CHANGELOG_CONTENT+="*No commits found in range ${COMMIT_RANGE}.*\n\n"
fi

if [[ "$DRY_RUN" = true ]]; then
    echo -e "$CHANGELOG_CONTENT"
else
    echo -e "$CHANGELOG_CONTENT" > "$OUTPUT_FILE"
    echo "Successfully generated $OUTPUT_FILE ($TAG_INFO)"
fi
