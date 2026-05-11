# generate-changelog

Generate a structured `CHANGELOG.md` from any project's git history. Auto-categorizes commits, groups by version, and produces clean markdown.

## Install (3 steps)

```bash
# 1. Copy the script to your project
cp skills/changelog/changelog.py /your/project/

# 2. Run it
python changelog.py

# 3. Review the generated CHANGELOG.md
```

Or use it as a Claude Code skill: copy `SKILL.md` to your project's `.claude/skills/` directory.

## Usage

```bash
# Since the last git tag
python changelog.py

# Since a specific version
python changelog.py --since v2.0.0

# Full history (no tags yet)
python changelog.py --full

# Custom output
python changelog.py --output RELEASES.md

# Different repo
python changelog.py --repo /path/to/project
```

## How categorization works

### Conventional commit prefixes

| Prefix | Category | Example |
|--------|----------|---------|
| `feat:` | **Added** | `feat: add user profile page` |
| `fix:` | **Fixed** | `fix: handle empty state on dashboard` |
| `refactor:` | **Changed** | `refactor: extract billing logic` |
| `perf:` | **Changed** | `perf: cache database queries` |
| `docs:` | **Changed** | `docs: update API reference` |
| `style:` | **Changed** | `style: format with prettier` |
| `test:` | **Changed** | `test: add unit tests for auth` |
| `chore:` | **Changed** | `chore: update dependencies` |
| `ci:` | **Changed** | `ci: add GitHub Actions workflow` |
| `build:` | **Changed** | `build: configure esbuild` |
| `revert:` | **Removed** | `revert: undo commit abc1234` |

### Natural language fallback

| Category | Matched prefixes |
|----------|-----------------|
| **Added** | `Add`, `New`, `Implement`, `Create`, `Introduce`, `Support`, `Enable` |
| **Fixed** | `Fix`, `Patch`, `Hotfix`, `Bugfix`, `Resolve`, `Correct` |
| **Removed** | `Remove`, `Delete`, `Drop`, `Deprecate`, `Revert`, `Cleanup`, `Purge` |
| **Changed** | `Update`, `Change`, `Refactor`, `Improve`, `Enhance`, `Upgrade`, `Migrate`, `Redesign`, `Simplify`, `Bump`, `Upgrade` |
| **Other** | Everything else |

## Requirements

- Python 3.8+
- git
