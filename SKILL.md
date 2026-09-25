# SKILL: Generate a structured CHANGELOG from git history

## Description
This skill provides a bash script `changelog.sh` that generates a structured `CHANGELOG.md`
file from the project's git commit history since the last git tag.

It categorizes commits by prefixes in the commit messages into:
- Added
- Fixed
- Changed
- Removed

The skill can be triggered via the `/generate-changelog` command or by running:

```bash
bash changelog.sh
```

## Usage

1. Run the script:

   ```bash
   bash changelog.sh
   ```

2. This will create or update a `CHANGELOG.md` file with the latest commits since the last git tag.

## Script: changelog.sh

```bash
#!/bin/bash

# Find the latest git tag
latest_tag=$(git describe --tags --abbrev=0 2>/dev/null)

# If no tags found, use the first commit as the start point
if [ -z "$latest_tag" ]; then
  range=""
  header_date=$(date +"%Y-%m-%d")
else
  range="$latest_tag..HEAD"
  header_date=$(date +"%Y-%m-%d")
fi

# Temporary files for categorized commits
added_tmp=$(mktemp)
fixed_tmp=$(mktemp)
changed_tmp=$(mktemp)
removed_tmp=$(mktemp)

# Extract commits since the last tag with message subject only
git log $range --pretty=format:"%s" | while read -r line; do
  case "$line" in
    Added:* | add:* | ADD:* )
      echo "- ${line#*: }" >> "$added_tmp"
      ;;
    Fixed:* | fix:* | FIX:* )
      echo "- ${line#*: }" >> "$fixed_tmp"
      ;;
    Changed:* | change:* | CHANGE:* )
      echo "- ${line#*: }" >> "$changed_tmp"
      ;;
    Removed:* | remove:* | REMOVE:* )
      echo "- ${line#*: }" >> "$removed_tmp"
      ;;
  esac
done

# Start building the changelog content
