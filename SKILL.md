---
name: generate-changelog
---

# Generate Changelog

A skill that generates a structured `CHANGELOG.md` from git commit history.

## Usage

In your project directory, run:

```bash
bash changelog.sh
```

Or specify a custom output path:

```bash
bash changelog.sh --output docs/CHANGELOG.md
```

## Requirements

- A git repository with conventional commit messages
- At least one git tag (or uses the first commit as fallback)

## Output

The script categorizes commits into:
- **Added** (`feat:`)
- **Fixed** (`fix:`)
- **Changed** (`refactor:`, `chore:`, `style:`, `perf:`, `docs:`)
- **Removed / Breaking** (`BREAKING CHANGE`)
