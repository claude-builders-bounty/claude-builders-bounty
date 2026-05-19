# Changelog Generator

Generate a structured `CHANGELOG.md` from git history using Conventional Commit prefixes.

## Quick Start

1. **Copy the files** into your project:
   ```bash
   cp changelog.sh generate_changelog.py skills/ -t your-project/
   ```

2. **Make it executable** (if not already):
   ```bash
   chmod +x changelog.sh generate_changelog.py
   ```

3. **Run it**:
   ```bash
   ./changelog.sh
   ```

That's it. A `CHANGELOG.md` is written to the current directory with all commits since the last git tag, auto-categorized.

## How It Works

The script fetches every commit since your latest git tag and categorizes each one by its Conventional Commit prefix:

| Commit Prefix | Changelog Section |
|---------------|-------------------|
| `feat:` | **Added** |
| `fix:` | **Fixed** |
| `refactor:`, `perf:`, `style:` | **Changed** |
| `revert:` | **Removed** |
| `docs:`, `test:`, `chore:`, `ci:` | **Other** |
| No recognized prefix | **Other** |

## Usage

```bash
# Basic: generate from latest tag
./changelog.sh

# Specify starting ref and version
./changelog.sh --since v1.0.0 --version v2.0.0

# Preview without writing
./changelog.sh --dry-run

# Write to a specific file
./changelog.sh --output RELEASE_NOTES.md

# Full help
./changelog.sh --help
```

## Flags

| Flag | Description |
|------|-------------|
| `-s`, `--since` | Git ref to start from (default: latest tag, or first commit) |
| `-v`, `--version` | Version string for the header (default: latest tag) |
| `-o`, `--output` | Output file path (default: `CHANGELOG.md`) |
| `-n`, `--dry-run` | Print to stdout without writing any file |

## Requirements

- Python 3.8+
- Git
- No dependencies beyond standard library

## Claude Code Integration

This project includes a Claude Code skill at `skills/generate-changelog/SKILL.md`.
Copy the `skills/` directory into your project to enable `/generate-changelog` inside Claude Code.
