# Generate Changelog

Automatically generate a structured `CHANGELOG.md` from your git history. Commits are categorized into **Added**, **Fixed**, **Changed**, and **Removed** sections using [conventional commit](https://www.conventionalcommits.org/) prefixes with intelligent keyword fallback.

Output follows the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

## Setup

### Option A: Bash Script

1. Copy `changelog.sh` into your project
2. Run `bash changelog.sh`
3. Open `CHANGELOG.md`

### Option B: Claude Code Skill

1. Copy `SKILL.md` to `.claude/commands/generate-changelog.md` in your project
2. Run `/generate-changelog` in Claude Code
3. Review the generated `CHANGELOG.md`

## How It Works

- Finds the latest git tag to determine the commit range
- If no tags exist, processes the entire commit history
- Categorizes each commit:

| Category    | Matched Prefixes                          | Keyword Fallback                        |
|-------------|-------------------------------------------|-----------------------------------------|
| **Added**   | `feat:`, `add:`, `new:`                   | add, create, introduce, implement       |
| **Fixed**   | `fix:`, `bugfix:`, `patch:`, `hotfix:`    | fix, resolve, repair, correct           |
| **Changed** | `refactor:`, `chore:`, `docs:`, `test:`, `perf:`, `ci:`, `build:`, `style:`, `update:`, `improve:`, `enhance:` | *(default)* |
| **Removed** | `remove:`, `delete:`, `drop:`, `deprecate:`, `revert:` | remove, delete, strip, drop   |

- Strips conventional commit prefixes for clean display
- Includes the short commit hash for traceability

## Usage

```bash
# Default: writes to CHANGELOG.md
bash changelog.sh

# Custom output path
bash changelog.sh docs/CHANGELOG.md
```

## Requirements

- Git
- Bash 3.2+ (default on macOS and Linux)
