#!/usr/bin/env bash
# ==============================================================================
# Automatic CHANGELOG Generator from Git History
# Complies with Opire Bounty #1 Acceptance Criteria
# ==============================================================================

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

# Get the latest git tag, or find the initial commit if no tags exist
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "${LATEST_TAG}" ]; then
    COMMIT_RANGE="${LATEST_TAG}..HEAD"
    VERSION_TITLE="Unreleased (since ${LATEST_TAG})"
else
    COMMIT_RANGE="HEAD"
    VERSION_TITLE="Initial Release"
fi

TODAY=$(date +"%Y-%m-%d")

# Temporary files for categories
TMP_DIR=$(mktemp -d)
trap 'rm -rf "${TMP_DIR}"' EXIT

ADDED_FILE="${TMP_DIR}/added.txt"
FIXED_FILE="${TMP_DIR}/fixed.txt"
CHANGED_FILE="${TMP_DIR}/changed.txt"
REMOVED_FILE="${TMP_DIR}/removed.txt"
OTHER_FILE="${TMP_DIR}/other.txt"

touch "${ADDED_FILE}" "${FIXED_FILE}" "${CHANGED_FILE}" "${REMOVED_FILE}" "${OTHER_FILE}"

# Read commits and categorize
git log ${COMMIT_RANGE} --pretty=format:"%s (%h by %an)" | while IFS= read -r line; do
    [ -z "${line}" ] && continue
    
    # Conventional commit prefixes & keyword matching
    LOWER_LINE=$(echo "${line}" | tr '[:upper:]' '[:lower:]')
    
    if [[ "${LOWER_LINE}" =~ ^feat(\(.*\))?: ]] || [[ "${LOWER_LINE}" =~ add|create|new ]]; then
        echo "- ${line}" >> "${ADDED_FILE}"
    elif [[ "${LOWER_LINE}" =~ ^fix(\(.*\))?: ]] || [[ "${LOWER_LINE}" =~ fix|bug|resolve|patch ]]; then
        echo "- ${line}" >> "${FIXED_FILE}"
    elif [[ "${LOWER_LINE}" =~ ^refactor(\(.*\))?: ]] || [[ "${LOWER_LINE}" =~ ^perf(\(.*\))?: ]] || [[ "${LOWER_LINE}" =~ update|change|modify|improve ]]; then
        echo "- ${line}" >> "${CHANGED_FILE}"
    elif [[ "${LOWER_LINE}" =~ ^revert(\(.*\))?: ]] || [[ "${LOWER_LINE}" =~ remove|delete|deprecate ]]; then
        echo "- ${line}" >> "${REMOVED_FILE}"
    else
        echo "- ${line}" >> "${OTHER_FILE}"
    fi
done

# Build CHANGELOG block
NEW_ENTRY=$(cat <<EOF
## [${VERSION_TITLE}] - ${TODAY}

EOF
)

has_entries=false

if [ -s "${ADDED_FILE}" ]; then
    NEW_ENTRY+=$'\n### Added\n'
    NEW_ENTRY+=$(cat "${ADDED_FILE}")
    has_entries=true
fi

if [ -s "${FIXED_FILE}" ]; then
    NEW_ENTRY+=$'\n\n### Fixed\n'
    NEW_ENTRY+=$(cat "${FIXED_FILE}")
    has_entries=true
fi

if [ -s "${CHANGED_FILE}" ]; then
    NEW_ENTRY+=$'\n\n### Changed\n'
    NEW_ENTRY+=$(cat "${CHANGED_FILE}")
    has_entries=true
fi

if [ -s "${REMOVED_FILE}" ]; then
    NEW_ENTRY+=$'\n\n### Removed\n'
    NEW_ENTRY+=$(cat "${REMOVED_FILE}")
    has_entries=true
fi

if [ -s "${OTHER_FILE}" ]; then
    NEW_ENTRY+=$'\n\n### Other Changes\n'
    NEW_ENTRY+=$(cat "${OTHER_FILE}")
    has_entries=true
fi

if [ "${has_entries}" = false ]; then
    NEW_ENTRY+=$'\n- No user-facing changes recorded in this range.\n'
fi

# Write to CHANGELOG.md (prepend or initialize)
HEADER="# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"

if [ ! -f "${OUTPUT_FILE}" ]; then
    echo -e "${HEADER}\n${NEW_ENTRY}\n" > "${OUTPUT_FILE}"
else
    # Prepend new entry under header
    TEMP_OUT="${TMP_DIR}/new_changelog.md"
    echo -e "${HEADER}\n${NEW_ENTRY}\n" > "${TEMP_OUT}"
    # Append previous entries (skipping existing header if present)
    grep -v "^# Changelog" "${OUTPUT_FILE}" | grep -v "^All notable changes" | grep -v "^The format is based" | grep -v "^and this project adheres" >> "${TEMP_OUT}" || true
    mv "${TEMP_OUT}" "${OUTPUT_FILE}"
fi

echo "✅ Successfully generated changelog in ${OUTPUT_FILE}"
