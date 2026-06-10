# Changelog Generator

A Claude Code skill that automatically generates a structured `CHANGELOG.md` from a project's git history.

## Usage
\`\`\`
/generate-changelog [from-tag]
\`\`\`

Or via shell:
\`\`\`bash
bash changelog-generator.sh v1.0.0
\`\`\`

## What it does
- Fetches commits since the last git tag
- Auto-categorizes into: Added / Fixed / Changed / Removed / Documentation / Other
- Outputs a properly formatted `CHANGELOG.md`
- Supports optional starting tag parameter

## Example output
See the script output for a formatted changelog with emoji-categorized sections.
