---
name: generate-changelog
description: Automatically generates a structured CHANGELOG.md from git history since the last tag, categorizing commits into Added, Fixed, Changed, and Removed.
---

# Generate Changelog Skill

This skill automates the extraction and categorization of git commit history into a standardized `CHANGELOG.md` following Keep a Changelog conventions.

## Execution

You can run this skill via the Claude Code command `/generate-changelog` or directly execute the accompanying shell script:

bash
./scripts/changelog.sh


## Implementation (`scripts/changelog.sh`)

Create the following script at `scripts/changelog.sh` and make it executable (`chmod +x scripts/changelog.sh`):

bash
#!/usr/bin/env bash
set -euo pipefail

# Configuration
OUTPUT_FILE="CHANGELOG.md"
VERSION_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo "HEAD")"
PREV_TAG="$(git describe --tags --abbrev=0 "${VERSION_TAG}^" 2>/dev/null || git rev-list --max-parents=0 HEAD)"

if [ "$VERSION_TAG" = "HEAD" ]; then
    RANGE="HEAD"
    TITLE="Unreleased"
else
    RANGE="${PREV_TAG}..HEAD"
    TITLE="[$VERSION_TAG] - $(date +%Y-%m-%d)"
fi

echo "Generating changelog for range: $RANGE"

# Temporary files for categories
ADDED=$(mktemp)
FIXED=$(mktemp)
CHANGED=$(mktemp)
REMOVED=$(mktemp)
OTHER=$(mktemp)

cleanup() {
    rm -f "$ADDED" "$FIXED" "$CHANGED" "$REMOVED" "$OTHER"
}
trap cleanup EXIT

# Extract commits (format: %s [hash])
while IFS= read -r line; do
    # Convert commit message to lowercase for matching
    lower=$(echo "$line" | tr '[:upper:]' '[:lower:]')
    
    if [[ "$lower" =~ ^feat ]] || [[ "$lower" =~ ^add ]] || [[ "$lower" =~ ^new ]]; then
        echo "- $line" >> "$ADDED"
    elif [[ "$lower" =~ ^fix ]] || [[ "$lower" =~ ^bug ]]; then
        echo "- $line" >> "$FIXED"
    elif [[ "$lower" =~ ^change ]] || [[ "$lower" =~ ^refactor ]] || [[ "$lower" =~ ^perf ]] || [[ "$lower" =~ ^update ]]; then
        echo "- $line" >> "$CHANGED"
    elif [[ "$lower" =~ ^remove ]] || [[ "$lower" =~ ^delete ]] || [[ "$lower" =~ ^deprecate ]]; then
        echo "- $line" >> "$REMOVED"
    else
        echo "- $line" >> "$OTHER"
    fi
done < <(git log "$RANGE" --no-merges --format="%s (%h)")

# Build the new changelog section
NEW_ENTRY="## $TITLE
"

if [ -s "$ADDED" ]; then
    NEW_ENTRY+="
### Added
"
    NEW_ENTRY+=$(cat "$ADDED")
    NEW_ENTRY+="
"
fi

if [ -s "$FIXED" ]; then
    NEW_ENTRY+="
### Fixed
"
    NEW_ENTRY+=$(cat "$FIXED")
    NEW_ENTRY+="
"
fi

if [ -s "$CHANGED" ]; then
    NEW_ENTRY+="
### Changed
"
    NEW_ENTRY+=$(cat "$CHANGED")
    NEW_ENTRY+="
"
fi

if [ -s "$REMOVED" ]; then
    NEW_ENTRY+="
### Removed
"
    NEW_ENTRY+=$(cat "$REMOVED")
    NEW_ENTRY+="
"
fi

if [ -s "$OTHER" ]; then
    NEW_ENTRY+="
### Other
"
    NEW_ENTRY+=$(cat "$OTHER")
    NEW_ENTRY+="
"
fi

# Prepend or update CHANGELOG.md
if [ ! -f "$OUTPUT_FILE" ]; then
    echo -e "# Changelog

All notable changes to this project will be documented in this file.

$NEW_ENTRY" > "$OUTPUT_FILE"
else
    # Insert after header (Line 3)
    TMP_CHANGELOG=$(mktemp)
    head -n 3 "$OUTPUT_FILE" > "$TMP_CHANGELOG"
    echo -e "
$NEW_ENTRY" >> "$TMP_CHANGELOG"
    tail -n +4 "$OUTPUT_FILE" >> "$TMP_CHANGELOG"
    mv "$TMP_CHANGELOG" "$OUTPUT_FILE"
fi

echo "Successfully updated $OUTPUT_FILE"


## Sample Output (`CHANGELOG.md`)

markdown
# Changelog

All notable changes to this project will be documented in this file.

## [v1.2.0] - 2025-05-18

### Added
- feat(auth): add OAuth2 login support (a1b2c3d)

### Fixed
- fix(database): resolve connection pool exhaustion under load (e4f5g6h)

### Changed
- refactor(api): migrate user endpoints to v2 router (j7k8l9m)

### Removed
- remove(legacy): drop deprecated v1 legacy endpoints (z1y2x3w)


## Setup Instructions

1. Copy the script to your repository:
   bash
   mkdir -p scripts skills/generate-changelog
   # Save the script above to scripts/changelog.sh
   chmod +x scripts/changelog.sh
   
2. Register the skill in your project's Claude Code configuration or execute directly via bash:
   bash
   ./scripts/changelog.sh
   
3. Commit your generated `CHANGELOG.md`:
   bash
   git add CHANGELOG.md && git commit -m "docs: update CHANGELOG.md"
   