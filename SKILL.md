# Generate Changelog

Generate a structured CHANGELOG.md from git commit history.

## Usage

```bash
/generate-changelog [since-tag]
```

## Examples

```bash
# Generate since last tag
/generate-changelog

# Generate since specific version
/generate-changelog v1.0.0

# View generated changelog
/cat CHANGELOG.md
```

## What It Does

1. Fetches commits since the last git tag (or specified tag)
2. Categorizes commits into Added/Fixed/Changed/Removed
3. Generates properly formatted CHANGELOG.md
4. Prepends to existing file (preserves history)

## Categories

- **Added**: New features (`feat:`, `add:`, `implement:`)
- **Fixed**: Bug fixes (`fix:`, `bugfix:`, `resolve:`)
- **Changed**: Updates (`docs:`, `refactor:`, `chore:`, `update:`)
- **Removed**: Deletions (`remove:`, `delete:`, `drop:`)

## Output Format

Follows [Keep a Changelog](https://keepachangelog.com/) format with emojis for visual scanning.
