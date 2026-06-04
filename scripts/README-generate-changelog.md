# Generate Changelog

Generate a structured `CHANGELOG.md` from commits since the latest git tag.

## Setup in 3 steps

1. Copy the scripts into any git repo:

   ```bash
   mkdir -p scripts && cp scripts/generate_changelog.py scripts/changelog.sh ./scripts/
   ```

2. Make the wrapper executable:

   ```bash
   chmod +x scripts/changelog.sh
   ```

3. Generate the changelog:

   ```bash
   bash scripts/changelog.sh --version "1.2.0"
   ```

## Usage

```bash
# Write CHANGELOG.md using commits since the latest tag
bash scripts/changelog.sh

# Pick a starting tag/ref explicitly
bash scripts/changelog.sh --since v1.0.0 --version v1.1.0

# Print to stdout instead of writing a file
bash scripts/changelog.sh --output -
```

## Categories

Commits are grouped into:

- `Added`
- `Fixed`
- `Changed`
- `Removed`

The script understands common Conventional Commit prefixes such as `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, and `ci:`. Non-matching commits fall back to `Changed`.

## Sample output

Generated from the git history in this repository:

```markdown
# Changelog

All notable changes to this project are documented in this file.

## Unreleased - 2026-06-04

### Changed

- Started by the Claude builder community · March 2026 · MIT License
```
