#!/usr/bin/env bash
# =============================================================================
# changelog.sh - Generate a structured CHANGELOG.md from git history
# =============================================================================
#
# Parses conventional commit messages and produces a Keep-a-Changelog
# formatted markdown file. Commits are categorized by their prefix:
#
#   feat:      -> Added
#   fix:       -> Fixed
#   refactor:  -> Changed
#   chore:     -> Changed
#   docs:      -> Changed
#   style:     -> Changed
#   perf:      -> Changed
#   revert:    -> Removed
#   remove:    -> Removed
#   delete:    -> Removed
#   (other)    -> Other
#
# Usage:
#   ./changelog.sh                  # output to stdout
#   ./changelog.sh -o CHANGELOG.md  # write to file
#   ./changelog.sh -t v1.0.0        # override "since" tag
#   ./changelog.sh -v 2.0.0         # set version label
#   ./changelog.sh -h               # show help
#
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
OUTPUT=""
SINCE_TAG=""
VERSION_LABEL=""
REPO_DIR="."

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
usage() {
    cat <<HELP
Usage: $(basename "$0") [OPTIONS]

Generate a CHANGELOG.md from git commit history using conventional commits.

Options:
  -o FILE    Write output to FILE instead of stdout
  -t TAG     Use TAG as the starting point (default: latest tag, or all commits)
  -v VERSION Label the release section with VERSION (default: Unreleased)
  -d DIR     Path to the git repository (default: current directory)
  -h         Show this help message

Examples:
  $(basename "$0")                        # print changelog to stdout
  $(basename "$0") -o CHANGELOG.md        # save to file
  $(basename "$0") -t v1.0.0 -v 2.0.0    # from tag v1.0.0, label as 2.0.0
HELP
    exit 0
}

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
while getopts ":o:t:v:d:h" opt; do
    case $opt in
        o) OUTPUT="$OPTARG" ;;
        t) SINCE_TAG="$OPTARG" ;;
        v) VERSION_LABEL="$OPTARG" ;;
        d) REPO_DIR="$OPTARG" ;;
        h) usage ;;
        \?) echo "Error: Unknown option -$OPTARG" >&2; exit 1 ;;
        :)  echo "Error: Option -$OPTARG requires an argument" >&2; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Validate that we are inside a git repository
# ---------------------------------------------------------------------------
if ! git -C "$REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: '$REPO_DIR' is not a git repository." >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Determine the commit range
# ---------------------------------------------------------------------------
if [[ -n "$SINCE_TAG" ]]; then
    if ! git -C "$REPO_DIR" rev-parse "$SINCE_TAG" >/dev/null 2>&1; then
        echo "Error: Tag '$SINCE_TAG' not found." >&2
        exit 1
    fi
    RANGE="${SINCE_TAG}..HEAD"
elif LATEST_TAG=$(git -C "$REPO_DIR" describe --tags --abbrev=0 2>/dev/null); then
    RANGE="${LATEST_TAG}..HEAD"
    SINCE_TAG="$LATEST_TAG"
else
    RANGE=""
    SINCE_TAG=""
fi

# ---------------------------------------------------------------------------
# Fetch commits (hash + full subject line)
# ---------------------------------------------------------------------------
if [[ -n "$RANGE" ]]; then
    COMMITS=$(git -C "$REPO_DIR" log "$RANGE" --pretty=format:"%H %s" 2>/dev/null || true)
else
    COMMITS=$(git -C "$REPO_DIR" log --pretty=format:"%H %s" 2>/dev/null || true)
fi

# Handle the "no commits" edge case
if [[ -z "$COMMITS" ]]; then
    NO_COMMITS_MSG="No commits found"
    [[ -n "$SINCE_TAG" ]] && NO_COMMITS_MSG="$NO_COMMITS_MSG since tag $SINCE_TAG"
    echo "$NO_COMMITS_MSG." >&2

    HEADER="# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [${VERSION_LABEL:-Unreleased}]

_No changes recorded._
"
    if [[ -n "$OUTPUT" ]]; then
        echo "$HEADER" > "$OUTPUT"
        echo "Empty changelog written to $OUTPUT" >&2
    else
        echo "$HEADER"
    fi
    exit 0
fi

# ---------------------------------------------------------------------------
# Categorize each commit
# ---------------------------------------------------------------------------
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

while IFS= read -r line; do
    HASH="${line%% *}"
    SUBJECT="${line#* }"
    SHORT_HASH="${HASH:0:7}"

    if [[ "$SUBJECT" =~ ^([a-zA-Z]+)(\(.+\))?!?:\ (.+)$ ]]; then
        PREFIX="${BASH_REMATCH[1]}"
        MESSAGE="${BASH_REMATCH[3]}"
    else
        PREFIX=""
        MESSAGE="$SUBJECT"
    fi

    PREFIX=$(echo "$PREFIX" | tr '[:upper:]' '[:lower:]')

    ENTRY="- ${MESSAGE} (\`${SHORT_HASH}\`)"

    case "$PREFIX" in
        feat|feature|add)
            ADDED+=("$ENTRY")
            ;;
        fix|bugfix|hotfix|patch)
            FIXED+=("$ENTRY")
            ;;
        refactor|chore|docs|style|perf|build|ci|test)
            CHANGED+=("$ENTRY")
            ;;
        revert|remove|delete|deprecate)
            REMOVED+=("$ENTRY")
            ;;
        *)
            OTHER+=("$ENTRY")
            ;;
    esac
done <<< "$COMMITS"

# ---------------------------------------------------------------------------
# Build the changelog output
# ---------------------------------------------------------------------------
TODAY=$(date +%Y-%m-%d)

if [[ -n "$VERSION_LABEL" ]]; then
    SECTION_TITLE="[${VERSION_LABEL}] - ${TODAY}"
else
    SECTION_TITLE="[Unreleased]"
fi

CHANGELOG="# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## ${SECTION_TITLE}
"

append_section() {
    local title="$1"
    shift
    local entries=("$@")
    if [[ ${#entries[@]} -gt 0 ]]; then
        CHANGELOG+="
### ${title}

"
        for entry in "${entries[@]}"; do
            CHANGELOG+="${entry}
"
        done
    fi
}

append_section "Added"   "${ADDED[@]+"${ADDED[@]}"}"
append_section "Fixed"   "${FIXED[@]+"${FIXED[@]}"}"
append_section "Changed" "${CHANGED[@]+"${CHANGED[@]}"}"
append_section "Removed" "${REMOVED[@]+"${REMOVED[@]}"}"
append_section "Other"   "${OTHER[@]+"${OTHER[@]}"}"

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
if [[ -n "$OUTPUT" ]]; then
    echo "$CHANGELOG" > "$OUTPUT"
    echo "Changelog written to $OUTPUT" >&2
else
    echo "$CHANGELOG"
fi
