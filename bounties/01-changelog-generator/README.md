# CHANGELOG Generator — Bounty #1 Submission

A Python-based changelog generator that auto-categorizes commits from git history.

## Files

- `generate_changelog.py` — main script (7.4 KB, 200 lines)
- `SKILL.md` — Claude Code skill wrapper
- `sample-output.md` — real example output from foundry-rs/foundry
- `README.md` — this file

## Installation (1 command)

```bash
# Just copy the script
cp generate_changelog.py /usr/local/bin/generate-changelog && chmod +x /usr/local/bin/generate-changelog
```

Or use as a Claude Code skill by copying `SKILL.md` to `~/.claude/skills/changelog-generator/`.

## Usage

```bash
# Generate CHANGELOG.md from latest tag
python3 generate_changelog.py

# From a specific tag
python3 generate_changelog.py --since v1.0.0

# All history (no tag filter)
python3 generate_changelog.py --all

# Custom output path
python3 generate_changelog.py --output HISTORY.md
```

## Acceptance Criteria (from issue #1)

- [x] Works via `/generate-changelog` (slash command) AND `python3 generate_changelog.py` (CLI)
- [x] Fetches commits since the last git tag (with `--all` fallback for repos without tags)
- [x] Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- [x] Outputs a properly formatted `CHANGELOG.md` (Markdown)
- [x] Tested on a real GitHub repo (see `sample-output.md` — foundry-rs/foundry, 21 commits)
- [x] README with setup instructions in 1 command

## Features

- **Conventional commit parsing** — recognizes `feat:`, `fix:`, `chore:`, etc.
- **Breaking change detection** — flags `feat!:` commits with ⚠️
- **Smart fallback** — works on repos without tags (uses all history)
- **Idempotent** — re-running inserts new entries above old ones
- **Zero dependencies** — pure Python 3.6+ stdlib
- **Cross-platform** — Linux, macOS, WSL

## Categorization Rules

| Pattern | Category |
|---|---|
| `feat:`, `add:`, `new:`, `implement:`, `introduce:`, `create:` | **Added** |
| `fix:`, `bug:`, `bugfix:`, `patch:`, `resolve:`, `repair:` | **Fixed** |
| `refactor:`, `update:`, `modify:`, `improve:`, `enhance:`, `optimize:`, `perf:`, `style:`, `docs:`, `chore:`, `build:`, `ci:`, `test:` | **Changed** |
| `remove:`, `delete:`, `drop:`, `deprecate:`, `revert:` | **Removed** |
| (other) | **Changed** (default) |

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-06-03

### Added
- add `msg-value-loop` (#15050)
- add `controlled-delegatecall` (#15046)

### Fixed
- identify forked contracts in debug traces (#15048)

### Changed
- update `solar` to latest main (#15003)
```

See `sample-output.md` for the full real-world example.

## Testing

```bash
# Clone a real repo
git clone --depth 50 https://github.com/foundry-rs/foundry.git /tmp/test
cd /tmp/test

# Run the generator
python3 /path/to/generate_changelog.py

# View result
head -30 CHANGELOG.md
```

## License

MIT
