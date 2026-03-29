#!/usr/bin/env bash
#
# changelog.sh - Generate a structured CHANGELOG.md from git history
#
# Usage:
#   bash changelog.sh [OPTIONS]
#
# Options:
#   -v, --version VERSION   Set the version header (default: auto-detect)
#   -o, --output FILE       Output file (default: CHANGELOG.md)
#   -r, --range RANGE       Git log range (default: last tag..HEAD or all commits)
#   -a, --append            Append to existing CHANGELOG.md instead of overwriting
#   -h, --help              Show this help message
#
set -euo pipefail

VERSION=""
OUTPUT="CHANGELOG.md"
RANGE=""
APPEND=false

usage() {
    sed -n '3,12p' "$0" | sed 's/^# \?//'
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -v|--version) VERSION="$2"; shift 2 ;;
        -o|--output)  OUTPUT="$2"; shift 2 ;;
        -r|--range)   RANGE="$2"; shift 2 ;;
        -a|--append)  APPEND=true; shift ;;
        -h|--help)    usage ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

# Ensure we're in a git repo
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "Error: not inside a git repository." >&2
    exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
OUTPUT_PATH="$REPO_ROOT/$OUTPUT"
TODAY="$(date +%Y-%m-%d)"

# Determine commit range
if [[ -z "$RANGE" ]]; then
    LATEST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
    if [[ -n "$LATEST_TAG" ]]; then
        RANGE="${LATEST_TAG}..HEAD"
    else
        RANGE="$(git rev-list --max-parents=0 HEAD)..HEAD"
        # If there's only one commit (the root), get all commits
        if [[ -z "$(git log "$RANGE" --oneline 2>/dev/null)" ]]; then
            RANGE=""
        fi
    fi
fi

# Determine version header
if [[ -z "$VERSION" ]]; then
    if [[ -n "${LATEST_TAG:-}" ]]; then
        VERSION="Unreleased"
    else
        VERSION="1.0.0"
    fi
fi

# Fetch commits
if [[ -n "$RANGE" ]]; then
    COMMITS="$(git log "$RANGE" --pretty=format:"%H|%s" --no-merges 2>/dev/null || true)"
else
    COMMITS="$(git log --pretty=format:"%H|%s" --no-merges 2>/dev/null || true)"
fi

if [[ -z "$COMMITS" ]]; then
    echo "No commits found in range. Nothing to generate."
    exit 0
fi

# Category arrays
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

# Strip conventional commit prefix from a message
strip_prefix() {
    local msg="$1"
    # Remove patterns like "feat: ", "fix(scope): ", "chore!: " etc.
    echo "$msg" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?!?:[[:space:]]*//'
}

# Categorize a commit message
categorize() {
    local hash="$1"
    local subject="$2"
    local short_hash="${hash:0:7}"
    local clean_msg
    clean_msg="$(strip_prefix "$subject")"
    # Capitalize first letter
    clean_msg="$(echo "${clean_msg:0:1}" | tr '[:lower:]' '[:upper:]')${clean_msg:1}"
    local entry="- ${clean_msg} (${short_hash})"
    local lower
    lower="$(echo "$subject" | tr '[:upper:]' '[:lower:]')"

    # Fixed (highest priority)
    if [[ "$lower" =~ ^fix[:] ]] || [[ "$lower" =~ ^fix\( ]] || \
       [[ "$lower" =~ ^bugfix[:] ]] || [[ "$lower" =~ ^bugfix\( ]] || \
       [[ "$lower" =~ (fix|bug|patch|resolve|correct|repair) ]]; then
        FIXED+=("$entry")
        return
    fi

    # Added
    if [[ "$lower" =~ ^feat[:] ]] || [[ "$lower" =~ ^feat\( ]] || \
       [[ "$lower" =~ ^add[:] ]] || [[ "$lower" =~ ^add\( ]] || \
       [[ "$lower" =~ (add|new|create|implement|introduce|support) ]]; then
        ADDED+=("$entry")
        return
    fi

    # Removed
    if [[ "$lower" =~ ^revert[:] ]] || [[ "$lower" =~ ^revert\( ]] || \
       [[ "$lower" =~ (remove|delete|deprecate|drop|cleanup|clean\ up) ]]; then
        REMOVED+=("$entry")
        return
    fi

    # Changed (default)
    CHANGED+=("$entry")
}

# Process each commit
while IFS= read -r line; do
    hash="${line%%|*}"
    subject="${line#*|}"
    categorize "$hash" "$subject"
done <<< "$COMMITS"

# Count total
TOTAL=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} ))

# Build the changelog section
SECTION=""
SECTION+="## [$VERSION] - $TODAY"$'\n'

if [[ ${#ADDED[@]} -gt 0 ]]; then
    SECTION+=$'\n'"### Added"$'\n'
    for e in "${ADDED[@]}"; do SECTION+="$e"$'\n'; done
fi

if [[ ${#FIXED[@]} -gt 0 ]]; then
    SECTION+=$'\n'"### Fixed"$'\n'
    for e in "${FIXED[@]}"; do SECTION+="$e"$'\n'; done
fi

if [[ ${#CHANGED[@]} -gt 0 ]]; then
    SECTION+=$'\n'"### Changed"$'\n'
    for e in "${CHANGED[@]}"; do SECTION+="$e"$'\n'; done
fi

if [[ ${#REMOVED[@]} -gt 0 ]]; then
    SECTION+=$'\n'"### Removed"$'\n'
    for e in "${REMOVED[@]}"; do SECTION+="$e"$'\n'; done
fi

# Header for new changelogs
HEADER="# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

"

# Write output
if [[ "$APPEND" == true ]] && [[ -f "$OUTPUT_PATH" ]]; then
    # Insert new section after the header block (after the first blank line following the preamble)
    # Find the line number of the first "## " heading or end of header
    EXISTING="$(cat "$OUTPUT_PATH")"
    # Check if file has the standard header
    if echo "$EXISTING" | head -1 | grep -q "^# Changelog"; then
        # Insert after the header (after the "based on Keep a Changelog" line + blank line)
        # Find the first ## line
        FIRST_SECTION_LINE="$(grep -n "^## " "$OUTPUT_PATH" | head -1 | cut -d: -f1 || true)"
        if [[ -n "$FIRST_SECTION_LINE" ]]; then
            {
                head -n $((FIRST_SECTION_LINE - 1)) "$OUTPUT_PATH"
                echo "$SECTION"
                tail -n +"$FIRST_SECTION_LINE" "$OUTPUT_PATH"
            } > "${OUTPUT_PATH}.tmp"
            mv "${OUTPUT_PATH}.tmp" "$OUTPUT_PATH"
        else
            # No existing sections, just append
            echo "" >> "$OUTPUT_PATH"
            echo "$SECTION" >> "$OUTPUT_PATH"
        fi
    else
        # No standard header, prepend everything
        {
            echo "${HEADER}${SECTION}"
            echo ""
            cat "$OUTPUT_PATH"
        } > "${OUTPUT_PATH}.tmp"
        mv "${OUTPUT_PATH}.tmp" "$OUTPUT_PATH"
    fi
else
    echo "${HEADER}${SECTION}" > "$OUTPUT_PATH"
fi

echo "Generated $OUTPUT_PATH"
echo "  Version: [$VERSION]"
echo "  Date:    $TODAY"
echo "  Commits: $TOTAL (Added: ${#ADDED[@]}, Fixed: ${#FIXED[@]}, Changed: ${#CHANGED[@]}, Removed: ${#REMOVED[@]})"
