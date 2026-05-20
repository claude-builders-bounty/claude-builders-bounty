# Changelog Generator

Generate a structured `CHANGELOG.md` from git history, auto-categorizing commits into Added / Fixed / Changed / Removed.

## Usage

### Option 1: Bash Script
```bash
bash changelog.sh [OPTIONS]
```

### Option 2: Claude Code Skill
Type `/generate-changelog` in Claude Code.

### Option 3: Python
```bash
python3 changelog.py [OPTIONS]
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `-t, --tag TAG` | Generate changelog since this tag | Last git tag |
| `-a, --all` | Generate full changelog (all tags) | Off |
| `-o, --output FILE` | Output file path | `CHANGELOG.md` |
| `-r, --repo PATH` | Path to git repository | Current directory |
| `--dry-run` | Print to stdout instead of file | Off |

## How It Works

1. Fetches commits since the last git tag (or specified tag)
2. Parses commit messages using [Conventional Commits](https://www.conventionalcommits.org/) format
3. Falls back to keyword-based categorization for non-conventional messages
4. Groups commits by category: `Added`, `Fixed`, `Changed`, `Removed`
5. Outputs a properly formatted `CHANGELOG.md` with links to commits

## Setup

1. Clone or download `changelog.sh` and `SKILL.md` into your project
2. Make executable: `chmod +x changelog.sh`
3. Run: `bash changelog.sh`

That's it. No dependencies required (uses only git and standard Unix tools).

## Commit Message Convention

For best results, use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add user authentication        → Added
fix: resolve login timeout issue     → Fixed
refactor: simplify DB query logic    → Changed
chore: remove deprecated API calls   → Removed
```

Non-conventional messages are auto-categorized by keywords:
- **Added**: "add", "create", "implement", "new", "introduce", "support"
- **Fixed**: "fix", "resolve", "repair", "patch", "correct", "debug"
- **Changed**: "update", "refactor", "improve", "enhance", "modify", "bump"
- **Removed**: "remove", "delete", "drop", "deprecate", "eliminate"
