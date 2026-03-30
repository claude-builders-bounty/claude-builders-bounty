# Changelog Generator

Generate a structured CHANGELOG.md from git history since the last tag.

## Usage

Run `/generate-changelog` or execute:
```bash
bash changelog.sh
```

## What It Does

1. Finds the last git tag (or uses first commit if no tags)
2. Collects all commits since that tag
3. Auto-categorizes commits into: Added, Fixed, Changed, Removed
4. Outputs a properly formatted CHANGELOG.md

## Categorization Rules

Commits are categorized by keywords in the commit message:

- **Added**: `add`, `feat`, `new`, `create`, `implement`, `introduce`
- **Fixed**: `fix`, `bug`, `patch`, `resolve`, `repair`, `correct`
- **Changed**: `change`, `update`, `modify`, `refactor`, `improve`, `enhance`, `rename`, `move`
- **Removed**: `remove`, `delete`, `drop`, `deprecate`, `clean`

Commits that don't match any category are placed under **Changed** by default.
