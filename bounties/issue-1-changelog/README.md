# generate-changelog

Generate a structured `CHANGELOG.md` from git history. Zero external dependencies.

## Setup

```bash
# Option 1: Direct
python3 bounties/issue-1-changelog/changelog.py

# Option 2: Claude Code skill
/generate-changelog
```

## Usage

```bash
python3 changelog.py                        # Write CHANGELOG.md
python3 changelog.py --dry-run              # Preview to stdout
python3 changelog.py --since v1.0.0         # Since a tag
python3 changelog.py --output HISTORY.md    # Custom file
python3 changelog.py --version 2.1.0        # Override version
```

## How it works

1. **Detects baseline**: Uses the latest git tag (or full history if no tags exist)
2. **Fetches commits**: `git log --no-merges` since baseline
3. **Classifies each commit** into categories using Conventional Commits + keyword matching
4. **Auto-detects version** from `package.json`, `pyproject.toml`, or `Cargo.toml`
5. **Writes** a Keep-a-Changelog formatted `CHANGELOG.md`

## Categories

| Prefix | Category |
|--------|----------|
| `feat:`, `add:`, `new:` | Added |
| `fix:`, `bug:`, `patch:` | Fixed |
| `refactor:`, `perf:`, `chore:`, `docs:`, `test:` | Changed |
| `remove:`, `delete:`, `deprecate:` | Removed |
| `security:`, `vuln:`, `CVE` | Security |

Unclassified commits default to **Changed**.

## Requirements

- Python 3.6+
- git (any version)
