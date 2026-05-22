# Generate Changelog

## Description

Generates a structured `CHANGELOG.md` from git history following the [keepachangelog.com](https://keepachangelog.com) format. Fetches commits since the last git tag (or all commits if no tags exist), auto-categorizes them by conventional commit prefixes, and outputs a properly formatted changelog.

## Usage

Run this skill with the `/generate-changelog` command.

## Implementation

When the user runs `/generate-changelog`, execute the following steps:

### Step 1: Determine the version range

```bash
# Get the latest git tag; if none exist, use the root commit
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -z "$LAST_TAG" ]; then
  RANGE="HEAD"
  FROM_DESC="the beginning"
else
  RANGE="${LAST_TAG}..HEAD"
  FROM_DESC="$LAST_TAG"
fi

# Get date range
if [ -z "$LAST_TAG" ]; then
  START_DATE=$(git log --reverse --format='%ai' | head -1 | cut -d' ' -f1)
else
  START_DATE=$(git log -1 --format='%ai' "$LAST_TAG" | cut -d' ' -f1)
fi
END_DATE=$(date +%Y-%m-%d)
```

### Step 2: Fetch and categorize commits

Collect all commits in the range and categorize them using these rules:

| Commit prefix | Category |
|---|---|
| `feat`, `feature`, `add` | Added |
| `fix`, `bugfix`, `patch` | Fixed |
| `refactor`, `change`, `update`, `improve` | Changed |
| `remove`, `delete`, `drop` | Removed |
| `docs`, `test`, `ci`, `chore`, `build`, `style`, `perf` | Other |
| _(no recognized prefix)_ | Other |

Parse commit messages in these formats:
- `type: description`
- `type(scope): description`

Extract the description part (after the colon) as the bullet text. If a scope is present, prepend it in bold: **scope**: description.

```bash
# Fetch commits as 'HASH|||SUBJECT' lines
if [ -z "$LAST_TAG" ]; then
  COMMITS=$(git log --format='%h|||%s' --reverse)
else
  COMMITS=$(git log --format='%h|||%s' --reverse "${RANGE}")
fi
```

### Step 3: Build the CHANGELOG.md

Categorize each commit and group them. Write the output in keepachangelog format:

```
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] - YYYY-MM-DD

### Added
- Description of added feature (HASH)

### Fixed
- Description of fix (HASH)

### Changed
- Description of change (HASH)

### Removed
- Description of removal (HASH)

### Other
- Description of other change (HASH)
```

Only include category sections that have at least one entry. Omit empty sections.

### Full script

Run this bash script to generate the changelog:

```bash
#!/usr/bin/env bash
set -euo pipefail

OUTPUT="CHANGELOG.md"

# --- Determine range ---
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -z "$LAST_TAG" ]; then
  RANGE=""
  FROM_DESC="the beginning"
else
  RANGE="${LAST_TAG}..HEAD"
  FROM_DESC="$LAST_TAG"
fi

END_DATE=$(date +%Y-%m-%d)

# --- Determine version label ---
# If there's a tag, label as Unreleased (changes since that tag)
# If no tag, label as Unreleased
VERSION_LABEL="Unreleased"

# --- Collect commits ---
if [ -z "$RANGE" ]; then
  COMMITS=$(git log --format='%h|||%s' --reverse 2>/dev/null || echo "")
else
  COMMITS=$(git log --format='%h|||%s' --reverse "$RANGE" 2>/dev/null || echo "")
fi

if [ -z "$COMMITS" ]; then
  echo "No commits found since ${FROM_DESC}. Nothing to generate."
  exit 0
fi

# --- Category arrays ---
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

# --- Categorize each commit ---
while IFS= read -r line; do
  HASH=$(echo "$line" | cut -d'|' -f1)
  SUBJECT=$(echo "$line" | sed 's/^[^|]*|||//')

  # Extract type, optional scope, and description
  if echo "$SUBJECT" | grep -qE '^[a-zA-Z]+(\([^)]*\))?:'; then
    TYPE=$(echo "$SUBJECT" | sed -E 's/^([a-zA-Z]+)(\([^)]*\))?\s*:.*/\1/' | tr '[:upper:]' '[:lower:]')
    SCOPE=$(echo "$SUBJECT" | sed -nE 's/^[a-zA-Z]+\(([^)]*)\)\s*:.*/\1/p')
    DESC=$(echo "$SUBJECT" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?\s*:\s*//')
  else
    TYPE=""
    DESC="$SUBJECT"
    SCOPE=""
  fi

  # Build bullet text
  if [ -n "$SCOPE" ]; then
    BULLET="- **${SCOPE}**: ${DESC} (\`${HASH}\`)"
  else
    BULLET="- ${DESC} (\`${HASH}\`)"
  fi

  # Categorize
  case "$TYPE" in
    feat|feature|add)
      ADDED="${ADDED}${BULLET}\n"
      ;;
    fix|bugfix|patch)
      FIXED="${FIXED}${BULLET}\n"
      ;;
    refactor|change|update|improve)
      CHANGED="${CHANGED}${BULLET}\n"
      ;;
    remove|delete|drop)
      REMOVED="${REMOVED}${BULLET}\n"
      ;;
    *)
      OTHER="${OTHER}${BULLET}\n"
      ;;
  esac
done <<< "$COMMITS"

# --- Write CHANGELOG.md ---
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""
  echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)."
  echo ""
  echo "## [${VERSION_LABEL}] - ${END_DATE}"
  echo ""

  if [ -n "$ADDED" ]; then
    echo "### Added"
    echo ""
    echo -e "${ADDED}"
  fi

  if [ -n "$FIXED" ]; then
    echo "### Fixed"
    echo ""
    echo -e "${FIXED}"
  fi

  if [ -n "$CHANGED" ]; then
    echo "### Changed"
    echo ""
    echo -e "${CHANGED}"
  fi

  if [ -n "$REMOVED" ]; then
    echo "### Removed"
    echo ""
    echo -e "${REMOVED}"
  fi

  if [ -n "$OTHER" ]; then
    echo "### Other"
    echo ""
    echo -e "${OTHER}"
  fi
} > "$OUTPUT"

echo "✅ Generated ${OUTPUT} with changes since ${FROM_DESC} (as of ${END_DATE})"
```

## Notes for Claude

- If the user specifies a version number (e.g., `/generate-changelog v1.2.0`), use that instead of "Unreleased" in the header.
- If the user asks to append rather than overwrite, insert the new section after the top-level `# Changelog` header and preamble, before any existing version sections.
- If there are no commits since the last tag, inform the user and do not create an empty changelog.
- Always preserve any existing content below the newly inserted section when appending.
