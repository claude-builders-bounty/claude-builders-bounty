#!/usr/bin/env bash
# ==============================================================================
# Automated Keep-a-Changelog Generator
# Scans commits since last git tag and updates CHANGELOG.md
# ==============================================================================
set -euo pipefail

TARGET_FILE="CHANGELOG.md"
TODAY=$(date +%Y-%m-%d)

# 1. Determine commit range
if git describe --tags --abbrev=0 >/dev/null 2>&1; then
    LATEST_TAG=$(git describe --tags --abbrev=0)
    RANGE="${LATEST_TAG}..HEAD"
    RELEASE_TITLE="[Unreleased] - ${TODAY} (since ${LATEST_TAG})"
else
    LATEST_TAG=""
    RANGE="HEAD"
    RELEASE_TITLE="[v0.1.0] - ${TODAY}"
fi

echo "🔍 Parsing git history (${RANGE})..."

# 2. Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r commit_line; do
    [ -z "$commit_line" ] && continue
    hash=$(echo "$commit_line" | awk '{print $1}')
    subject=$(echo "$commit_line" | cut -d' ' -f2-)

    lower_subject=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

    if [[ "$lower_subject" =~ ^(feat|add|feature|new)(\(.*\))?: ]]; then
        clean_msg=$(echo "$subject" | sed -E 's/^(feat|add|feature|new)(\(.*\))?:[[:space:]]*//I')
        ADDED="${ADDED}- ${clean_msg} (\`${hash}\`)\n"
    elif [[ "$lower_subject" =~ ^(fix|bug|patch|resolve)(\(.*\))?: ]]; then
        clean_msg=$(echo "$subject" | sed -E 's/^(fix|bug|patch|resolve)(\(.*\))?:[[:space:]]*//I')
        FIXED="${FIXED}- ${clean_msg} (\`${hash}\`)\n"
    elif [[ "$lower_subject" =~ ^(remove|deprecate|delete|rm)(\(.*\))?: ]]; then
        clean_msg=$(echo "$subject" | sed -E 's/^(remove|deprecate|delete|rm)(\(.*\))?:[[:space:]]*//I')
        REMOVED="${REMOVED}- ${clean_msg} (\`${hash}\`)\n"
    else
        CHANGED="${CHANGED}- ${subject} (\`${hash}\`)\n"
    fi
done < <(git log --oneline --no-merges "${RANGE}")

# 3. Format New Section
NEW_SECTION="## ${RELEASE_TITLE}\n\n"

if [ -n "$ADDED" ]; then
    NEW_SECTION="${NEW_SECTION}### Added\n${ADDED}\n"
fi
if [ -n "$FIXED" ]; then
    NEW_SECTION="${NEW_SECTION}### Fixed\n${FIXED}\n"
fi
if [ -n "$CHANGED" ]; then
    NEW_SECTION="${NEW_SECTION}### Changed\n${CHANGED}\n"
fi
if [ -n "$REMOVED" ]; then
    NEW_SECTION="${NEW_SECTION}### Removed\n${REMOVED}\n"
fi

# 4. Write to CHANGELOG.md
TMP_FILE=$(mktemp)
echo "# Changelog" > "$TMP_FILE"
echo "" >> "$TMP_FILE"
echo "All notable changes to this project will be documented in this file." >> "$TMP_FILE"
echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)." >> "$TMP_FILE"
echo "" >> "$TMP_FILE"
echo -e "$NEW_SECTION" >> "$TMP_FILE"

if [ -f "$TARGET_FILE" ]; then
    # Append previous entries (skipping existing header)
    awk 'NR>4 {print}' "$TARGET_FILE" >> "$TMP_FILE" || true
fi

mv "$TMP_FILE" "$TARGET_FILE"
echo "✅ Successfully updated ${TARGET_FILE}"
