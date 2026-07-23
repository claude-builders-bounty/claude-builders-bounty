---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag.
---

# Generate Changelog

Auto-generates a `CHANGELOG.md` categorized into Added / Fixed / Changed / Removed by analyzing commit messages since the last git tag.

## Usage

```
/generate-changelog
```

Or:

```bash
python changelog.py
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--repo <path>` | `.` | Path to the git repository |
| `--output <file>` | `CHANGELOG.md` | Output file path |

## Example Output

```markdown
# Changelog

## [v14.2.6] - 2026-03-03

### Changed
- chore: add changeset (#854)
- Switch package manager to pnpm 10 (#853)

### Fixed
- replace clipboardy with tinyclip (#848)
```

## Requirements

- Python 3.8+
- `git` on PATH
- A git repository with commits (tags optional)
