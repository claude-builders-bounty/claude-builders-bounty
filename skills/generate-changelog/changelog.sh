#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Complies with Claude Code /generate-changelog specification

set -euo pipefail

REPO_DIR="${1:-.}"
OUTPUT_FILE="${2:-CHANGELOG.md}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# If python3 is available, run the comprehensive Python engine
if command -v python3 >/dev/null 2>&1 && [ -f "${SCRIPT_DIR}/changelog_generator.py" ]; then
    python3 "${SCRIPT_DIR}/changelog_generator.py" --repo "${REPO_DIR}" --output "${OUTPUT_FILE}"
    echo "✅ CHANGELOG generated at ${OUTPUT_FILE} (via Python engine)"
    exit 0
fi

# Fallback: Zero-dependency pure Bash generator
cd "${REPO_DIR}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: ${REPO_DIR} is not a valid git repository" >&2
    exit 1
fi

LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
DATE_STR=$(date +"%Y-%m-%d")

cat <<EOF > "${OUTPUT_FILE}"
# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - ${DATE_STR}

EOF

if [ -n "${LATEST_TAG}" ]; then
    RANGE="${LATEST_TAG}..HEAD"
    echo "> Commits since ${LATEST_TAG}:" >> "${OUTPUT_FILE}"
else
    RANGE="HEAD"
    echo "> Initial release history:" >> "${OUTPUT_FILE}"
fi

declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a OTHER=()

while IFS= read -r line; do
    [ -z "$line" ] && continue
    if [[ "$line" =~ ^feat(\(.*\))?!?:[[:space:]]*(.*) ]]; then
        ADDED+=("- ${BASH_REMATCH[2]}")
    elif [[ "$line" =~ ^fix(\(.*\))?!?:[[:space:]]*(.*) ]]; then
        FIXED+=("- ${BASH_REMATCH[2]}")
    elif [[ "$line" =~ ^(refactor|perf|style)(\(.*\))?!?:[[:space:]]*(.*) ]]; then
        CHANGED+=("- ${BASH_REMATCH[3]}")
    elif [[ "$line" =~ ^revert(\(.*\))?!?:[[:space:]]*(.*) ]]; then
        REMOVED+=("- ${BASH_REMATCH[2]}")
    else
        OTHER+=("- ${line}")
    fi
done < <(git log "${RANGE}" --no-merges --format="%s")

if [ ${#ADDED[@]} -gt 0 ]; then
    echo -e "\n### Added" >> "${OUTPUT_FILE}"
    printf '%s\n' "${ADDED[@]}" >> "${OUTPUT_FILE}"
fi

if [ ${#FIXED[@]} -gt 0 ]; then
    echo -e "\n### Fixed" >> "${OUTPUT_FILE}"
    printf '%s\n' "${FIXED[@]}" >> "${OUTPUT_FILE}"
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
    echo -e "\n### Changed" >> "${OUTPUT_FILE}"
    printf '%s\n' "${CHANGED[@]}" >> "${OUTPUT_FILE}"
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
    echo -e "\n### Removed" >> "${OUTPUT_FILE}"
    printf '%s\n' "${REMOVED[@]}" >> "${OUTPUT_FILE}"
fi

if [ ${#OTHER[@]} -gt 0 ]; then
    echo -e "\n### Other Changes" >> "${OUTPUT_FILE}"
    printf '%s\n' "${OTHER[@]}" >> "${OUTPUT_FILE}"
fi

echo "✅ CHANGELOG generated at ${OUTPUT_FILE} (via pure Bash engine)"
