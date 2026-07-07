# Changelog Generator Skill

Generate a structured CHANGELOG.md from git history.

## Usage

\`\`\`bash
/generate-changelog
# or
bash changelog.sh [output-file]
\`\`\`

## Description

This skill automatically generates a structured CHANGELOG.md from a project's git history.
It fetches commits since the last git tag and auto-categorizes them into:

- **Added**: New features (feat, add, new, create, implement)
- **Fixed**: Bug fixes (fix, bug, hotfix, patch)
- **Changed**: Modifications (default category)
- **Removed**: Deletions (remove, delete, drop, deprecate)

## Output

Produces a properly formatted CHANGELOG.md with version headers, dates, and categorized commit messages.
