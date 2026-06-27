# generate-changelog

Generate a structured `CHANGELOG.md` from git history in seconds.

## Setup — 2 steps

**Step 1:** Copy `changelog.py` and `changelog.sh` to your project root.

**Step 2:** Run it.

```bash
bash changelog.sh
```

That's it. `CHANGELOG.md` is written to your project root.

## Usage

```bash
# Auto-detect last git tag as baseline
bash changelog.sh

# From a specific tag
bash changelog.sh v1.2.0

# Preview without writing
python changelog.py --dry-run

# Print to stdout
python changelog.py --output -

# Last 14 days
python changelog.py --days 14
```

## Claude Code skill

Use `/generate-changelog` via the included `SKILL.md`.

Copy `SKILL.md` to your `.claude/skills/` directory and Claude Code will automatically understand the `/generate-changelog` command.

## Output format

Follows [Keep a Changelog](https://keepachangelog.com) with these sections:

| Section | Triggered by |
|---------|-------------|
| `### Added` | `feat:`, `add:`, `new:` prefixes |
| `### Fixed` | `fix:`, `bug:`, `hotfix:` prefixes |
| `### Changed` | `refactor:`, `update:`, `chore:`, `perf:` prefixes |
| `### Removed` | `remove:`, `delete:`, `drop:` prefixes |
| `### Docs` | `docs:`, `doc:` prefixes |

Also recognizes GitHub labels (`enhancement`, `bug`, etc.) when `GITHUB_TOKEN` is set.

## Requirements

- Python 3.9+
- Git repository with at least one commit
