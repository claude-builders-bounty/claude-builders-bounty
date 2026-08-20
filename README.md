# Structured Git CHANGELOG Generator (Keep a Changelog 1.1.0)

Automated tool and Claude Code Skill to generate clean, categorized `CHANGELOG.md` files from Git commits.

## Features
- **Keep a Changelog Standard**: Categorizes into `Added`, `Changed`, `Fixed`, `Removed`.
- **Automatic Tag Discovery**: Generates diffs since the latest git tag automatically if not specified.
- **Dual Support**: Works as a native Claude Code Skill (`/generate-changelog`) or standalone CLI script (`changelog.sh`).

## Quickstart in 3 Steps

### 1. Installation
Clone the repository or copy `changelog.sh` into your project root:
```bash
chmod +x changelog.sh
```

### 2. Generate Changelog
Run the script directly:
```bash
# Generate changelog since the latest git tag
./changelog.sh

# Or specify custom tag range and output file
./changelog.sh --since v1.0.0 --output CHANGELOG.md
```

### 3. Claude Code Skill Setup (Optional)
Place `SKILL.md` in your project's `.claude/skills/` or invoke `/generate-changelog`.

## Sample Output
See `sample_changelog.md` for an example of the generated changelog format.
