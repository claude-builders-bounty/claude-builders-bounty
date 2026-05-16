# changelog-generator

Generate a structured `CHANGELOG.md` from your git history in one command.

## Setup

1. Copy `changelog.py` into your project
2. (Optional) Copy `SKILL.md` into your `.hermes/skills/` for Claude Code integration

## Usage

```bash
python3 changelog.py --output CHANGELOG.md
```

## Options

| Flag | Description |
|------|-------------|
| `--output`, `-o` | Write to file instead of stdout |
| `--since` | Starting point (tag, commit, or date). Default: last git tag |
| `--repo` | Path to another git repo (default: current directory) |
| `--version` | Version string (default: auto-detected from tags) |

## Commit Format

Works best with [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add user authentication        → Added
fix: resolve redirect loop            → Fixed
refactor!: restructure API            → Changed (breaking)
docs: update README                   → Documentation
chore: bump dependencies              → Maintenance
test: add api tests                   → Maintenance
```
