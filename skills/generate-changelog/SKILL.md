---
name: generate-changelog
description: Automatically generates a structured, Keep a Changelog-compliant CHANGELOG.md from git commits since the last release tag.
---

# Generate Changelog Skill

This skill analyzes git commits in the current repository since the most recent git tag (or from the initial commit if untagged) and generates or updates a `CHANGELOG.md` file organized by standard Keep a Changelog categories:
- **Added**: New features and capabilities (`feat:`, `add:`, `implement:`)
- **Fixed**: Bug fixes and error resolutions (`fix:`, `patch:`, `resolve:`)
- **Changed**: Refactoring, performance improvements, and modifications (`refactor:`, `perf:`, `update:`)
- **Removed**: Deprecated or deleted functionality (`remove:`, `delete:`, `deprecate:`)
- **Maintenance & Chores**: Dependency updates, tests, and build tooling

## Usage

### 1. Interactive Skill Execution
Run within Claude Code:
```
/generate-changelog [output_file] [version_tag]
```
- Defaults:
  - `output_file`: `CHANGELOG.md`
  - `version_tag`: `Unreleased` (or pass specific version like `1.2.0`)

### 2. Standalone Shell Script Execution
```bash
# Make executable
chmod +x changelog.sh

# Generate for unreleased changes
./changelog.sh

# Generate for a specific release version
./changelog.sh CHANGELOG.md 1.2.0
```

## How It Works

1. **Tag Detection**: Checks `git describe --tags --abbrev=0`.
   - If a tag exists (e.g. `v1.1.0`), commits are scanned in `v1.1.0..HEAD`.
   - If no tag exists, all non-merge commits in repository history are processed.
2. **Commit Parsing**: Filters out merge commits and parses Conventional Commits and semantic keywords.
3. **Markdown Construction**: Formats markdown with date and commit hashes for traceable auditing.
4. **Idempotent Prepends**: If `CHANGELOG.md` already exists, inserts the new version section directly under the `# Changelog` header without overwriting previous release history.
