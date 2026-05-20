#!/bin/bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since TAG] [--output FILE] [--repo PATH]
# Bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1

set -euo pipefail

SINCE=""
OUTPUT="CHANGELOG.md"
REPO="$(pwd)"

show_help() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Generate a structured CHANGELOG.md from git history with conventional-commit awareness.

Options:
  --since TAG     Start from this tag (default: auto-detect last tag)
  --output FILE   Output file (default: CHANGELOG.md)
  --repo PATH     Path to git repository (default: current dir)
  --help          Show this help
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --since) SINCE="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        --repo) REPO="$2"; shift 2 ;;
        --help) show_help ;;
        *) echo "Error: Unknown option: $1" >&2; exit 1 ;;
    esac
done

if ! git -C "$REPO" rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not a git repository: $REPO" >&2
    exit 1
fi

if [[ -z "$SINCE" ]]; then
    SINCE=$(git -C "$REPO" describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [[ -n "$SINCE" ]]; then
    RANGE="${SINCE}..HEAD"
    HEADER_LINE="## [Unreleased] (since ${SINCE})"
else
    RANGE="HEAD"
    HEADER_LINE="## [Unreleased] (initial commit)"
fi

COMMIT_COUNT=$(git -C "$REPO" rev-list "$RANGE" --count 2>/dev/null || echo 0)
if [[ "$COMMIT_COUNT" -eq 0 ]]; then
    echo "No new commits since ${SINCE:-beginning}." >&2
    exit 0
fi

echo "Found $COMMIT_COUNT commits in range ${RANGE}"

ADDED=(); FIXED=(); CHANGED=(); REMOVED=(); OTHER=()

while IFS='|' read -r hash message; do
    type=""; desc="$message"
    if [[ "$message" =~ ^([a-z]+)(\([^)]+\))?!?:\ (.*) ]]; then
        type="${BASH_REMATCH[1]}"; desc="${BASH_REMATCH[3]}"
    fi
    entry="- ${desc} (${hash:0:7})"
    case "$type" in
        feat|feature) ADDED+=("$entry") ;;
        fix|bugfix)   FIXED+=("$entry") ;;
        change|refactor|perf|style) CHANGED+=("$entry") ;;
        remove|deprecate) REMOVED+=("$entry") ;;
        *)             OTHER+=("$entry") ;;
    esac
done < <(git -C "$REPO" log --format="%H|%s" "$RANGE" 2>/dev/null || true)

{
    echo "# Changelog"; echo ""
    echo "$HEADER_LINE"; echo ""
    if [[ ${#ADDED[@]} -gt 0 ]]; then echo "### Added"; for item in "${ADDED[@]}"; do echo "$item"; done; echo ""; fi
    if [[ ${#FIXED[@]} -gt 0 ]]; then echo "### Fixed"; for item in "${FIXED[@]}"; do echo "$item"; done; echo ""; fi
    if [[ ${#CHANGED[@]} -gt 0 ]]; then echo "### Changed"; for item in "${CHANGED[@]}"; do echo "$item"; done; echo ""; fi
    if [[ ${#REMOVED[@]} -gt 0 ]]; then echo "### Removed"; for item in "${REMOVED[@]}"; do echo "$item"; done; echo ""; fi
    if [[ ${#OTHER[@]} -gt 0 ]]; then echo "### Other"; for item in "${OTHER[@]}"; do echo "$item"; done; echo ""; fi
} > "$OUTPUT"

echo "Generated $OUTPUT (Added: ${#ADDED[@]}, Fixed: ${#FIXED[@]}, Changed: ${#CHANGED[@]}, Removed: ${#REMOVED[@]})"
