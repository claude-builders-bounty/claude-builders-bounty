#!/usr/bin/env bash
# generate-changelog: Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since TAG] [--output FILE]
#
# Options:
#   --since TAG    Generate changelog since this tag (default: last tag)
#   --output FILE  Output file path (default: CHANGELOG.md)
#   --unreleased   Label the section as "Unreleased" instead of a version
#   --help         Show this help message

set -euo pipefail

SINCE=""
OUTPUT="CHANGELOG.md"
UNRELEASED=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --since) SINCE="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        --unreleased) UNRELEASED=true; shift ;;
        --help)
            sed -n '2,9p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Find the script directory for the Python parser
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Determine the starting point
if [[ -z "$SINCE" ]]; then
    SINCE=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# Get commits
if [[ -n "$SINCE" ]]; then
    COMMITS=$(git log "${SINCE}..HEAD" --pretty=format:"%H|||%s|||%an|||%ad" --date=short 2>/dev/null)
else
    COMMITS=$(git log --pretty=format:"%H|||%s|||%an|||%ad" --date=short 2>/dev/null)
fi

if [[ -z "$COMMITS" ]]; then
    echo "No commits found since ${SINCE:-beginning}."
    exit 0
fi

# Determine version header
if [[ "$UNRELEASED" == true ]]; then
    VERSION="Unreleased"
else
    # Try to get next version from latest tag
    if [[ -n "$SINCE" ]]; then
        VERSION="$SINCE → HEAD"
    else
        VERSION="$(git describe --tags 2>/dev/null || echo 'Unreleased')"
    fi
fi

# Pass to Python categorizer
echo "$COMMITS" | python3 "${SCRIPT_DIR}/categorize.py" --version "$VERSION" --output "$OUTPUT"

echo "Generated: $OUTPUT"
