#!/usr/bin/env bash
# ==============================================================================
# changelog.sh — Automated Structured CHANGELOG.md Generator
# Categorizes Git history since last tag into Added / Fixed / Changed / Removed
# ==============================================================================

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
NEW_VERSION="${2:-Unreleased}"
TODAY=$(date +%Y-%m-%d)

echo "🔍 Generating changelog into ${OUTPUT_FILE} for version [${NEW_VERSION}] (${TODAY})..."

# 1. Identify previous git tag
if git describe --tags --abbrev=0 >/dev/null 2>&1; then
  LAST_TAG=$(git describe --tags --abbrev=0)
  REVISION_RANGE="${LAST_TAG}..HEAD"
  echo "📌 Found last git tag: ${LAST_TAG}. Reading commits in range: ${REVISION_RANGE}"
else
  LAST_TAG=""
  REVISION_RANGE="HEAD"
  echo "ℹ️ No previous git tags found. Processing all repository commits..."
fi

# 2. Extract commits in format: HASH|SUBJECT
COMMITS=$(git log "${REVISION_RANGE}" --no-merges --pretty=format:"%h|%s" || true)

if [ -z "${COMMITS}" ]; then
  echo "⚠️ No new commits found since ${LAST_TAG:-initial commit}."
  exit 0
fi

# Temporary arrays / files for categorization
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

while IFS='|' read -r HASH SUBJECT; do
  [ -z "${HASH}" ] && continue

  # Match prefixes (case-insensitive)
  LOWER_SUB=$(echo "${SUBJECT}" | tr '[:upper:]' '[:lower:]')

  if [[ "${LOWER_SUB}" =~ ^(feat|add|feature)(\(.*\))?:\ ? ]]; then
    CLEAN=$(echo "${SUBJECT}" | sed -E 's/^(feat|add|feature)(\([^)]+\))?:[[:space:]]*//I')
    ADDED+=("- ${CLEAN} (\`${HASH}\`)")
  elif [[ "${LOWER_SUB}" =~ ^(fix|bug|patch|resolve|fixed)(\(.*\))?:\ ? ]]; then
    CLEAN=$(echo "${SUBJECT}" | sed -E 's/^(fix|bug|patch|resolve|fixed)(\([^)]+\))?:[[:space:]]*//I')
    FIXED+=("- ${CLEAN} (\`${HASH}\`)")
  elif [[ "${LOWER_SUB}" =~ ^(refactor|perf|change|update|mod)(\(.*\))?:\ ? ]]; then
    CLEAN=$(echo "${SUBJECT}" | sed -E 's/^(refactor|perf|change|update|mod)(\([^)]+\))?:[[:space:]]*//I')
    CHANGED+=("- ${CLEAN} (\`${HASH}\`)")
  elif [[ "${LOWER_SUB}" =~ ^(remove|delete|deprecate)(\(.*\))?:\ ? ]]; then
    CLEAN=$(echo "${SUBJECT}" | sed -E 's/^(remove|delete|deprecate)(\([^)]+\))?:[[:space:]]*//I')
    REMOVED+=("- ${CLEAN} (\`${HASH}\`)")
  else
    # Fallback heuristic: check if keywords exist in message
    if [[ "${LOWER_SUB}" == *"add"* || "${LOWER_SUB}" == *"create"* || "${LOWER_SUB}" == *"implement"* ]]; then
      ADDED+=("- ${SUBJECT} (\`${HASH}\`)")
    elif [[ "${LOWER_SUB}" == *"fix"* || "${LOWER_SUB}" == *"bug"* || "${LOWER_SUB}" == *"error"* || "${LOWER_SUB}" == *"prevent"* ]]; then
      FIXED+=("- ${SUBJECT} (\`${HASH}\`)")
    elif [[ "${LOWER_SUB}" == *"refactor"* || "${LOWER_SUB}" == *"clean"* || "${LOWER_SUB}" == *"update"* ]]; then
      CHANGED+=("- ${SUBJECT} (\`${HASH}\`)")
    elif [[ "${LOWER_SUB}" == *"remove"* || "${LOWER_SUB}" == *"delete"* ]]; then
      REMOVED+=("- ${SUBJECT} (\`${HASH}\`)")
    else
      OTHER+=("- ${SUBJECT} (\`${HASH}\`)")
    fi
  fi
done <<< "${COMMITS}"

# 3. Assemble Markdown section
SECTION="## [${NEW_VERSION}] - ${TODAY}

"

if [ ${#ADDED[@]} -gt 0 ]; then
  SECTION="${SECTION}### Added
"
  for item in "${ADDED[@]}"; do
    SECTION="${SECTION}${item}
"
  done
  SECTION="${SECTION}
"
fi

if [ ${#FIXED[@]} -gt 0 ]; then
  SECTION="${SECTION}### Fixed
"
  for item in "${FIXED[@]}"; do
    SECTION="${SECTION}${item}
"
  done
  SECTION="${SECTION}
"
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
  SECTION="${SECTION}### Changed
"
  for item in "${CHANGED[@]}"; do
    SECTION="${SECTION}${item}
"
  done
  SECTION="${SECTION}
"
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
  SECTION="${SECTION}### Removed
"
  for item in "${REMOVED[@]}"; do
    SECTION="${SECTION}${item}
"
  done
  SECTION="${SECTION}
"
fi

if [ ${#OTHER[@]} -gt 0 ]; then
  SECTION="${SECTION}### Maintenance & Chores
"
  for item in "${OTHER[@]}"; do
    SECTION="${SECTION}${item}
"
  done
  SECTION="${SECTION}
"
fi

# 4. Write or prepend to CHANGELOG.md
if [ -f "${OUTPUT_FILE}" ]; then
  # Prepend under the main title if file exists
  TEMP_FILE=$(mktemp)
  if grep -q "^# Changelog" "${OUTPUT_FILE}"; then
    awk -v sec="${SECTION}" '
      /^# Changelog/ { print; print ""; print sec; next }
      { print }
    ' "${OUTPUT_FILE}" > "${TEMP_FILE}"
    mv "${TEMP_FILE}" "${OUTPUT_FILE}"
  else
    printf "# Changelog\n\n%s\n%s" "${SECTION}" "$(cat "${OUTPUT_FILE}")" > "${OUTPUT_FILE}"
  fi
else
  # Create new file with standard Keep a Changelog header
  cat <<EOF > "${OUTPUT_FILE}"
# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

${SECTION}
EOF
fi

echo "✅ Successfully generated changelog in ${OUTPUT_FILE}!"
