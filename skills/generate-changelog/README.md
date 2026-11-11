# Generate Changelog Skill & Tool

Automatically generate Keep a Changelog compliant `CHANGELOG.md` files from git history.

## Features
- **Zero External Dependencies**: Pure bash/git and standard library Python.
- **Conventional Commit Parsing**: Automatically categorizes `feat` → `Added`, `fix` → `Fixed`, `remove/deprecate` → `Removed`, `chore/refactor/docs` → `Changed`.
- **Flexible Ranges**: Auto-detects the latest git tag, or generates full repository history with `--all`.
- **Claude Code Native**: Includes `SKILL.md` for seamless `/generate-changelog` command usage.

## Setup & Quick Start (3 Steps)

1. **Copy or link `changelog.sh` to your repo**:
   ```bash
   chmod +x skills/generate-changelog/changelog.sh
   ```

2. **Run the generator**:
   ```bash
   ./skills/generate-changelog/changelog.sh
   ```

3. **(Optional) Run in Claude Code**:
   Add this skill to your `.claude/skills/` directory and invoke `/generate-changelog`.

## CLI Options

```bash
Usage: changelog.sh [OPTIONS]

Options:
  -o, --output FILE    Output changelog file (default: CHANGELOG.md)
  -t, --tag TAG        Generate changelog since a specific tag
  -a, --all            Include all commits from initial commit
  -d, --dry-run        Print changelog to stdout without writing file
  -h, --help           Show help message
```
