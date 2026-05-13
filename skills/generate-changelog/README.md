# generate-changelog

Generate a structured `CHANGELOG.md` from git history, auto-categorized into Added / Fixed / Changed / Removed.

## Setup

1. Copy `skills/generate-changelog/` into your project
2. Run: `bash skills/generate-changelog/changelog.sh`
3. Open `CHANGELOG.md` to review

## Usage

**As a bash script:**

```bash
bash changelog.sh                     # default: since last tag → CHANGELOG.md
bash changelog.sh --tag v1.0.0        # since a specific tag
bash changelog.sh --output CHANGES.md # custom output file
```

**As a Claude Code skill:**

```
/generate-changelog
```

## How It Works

The script reads `git log` since the latest tag (or full history if no tags exist) and classifies each commit by its first word:

| Prefix | Category |
|--------|----------|
| `feat`, `add`, `new`, `create`, `implement`, `introduce`, `support` | **Added** |
| `fix`, `bug`, `patch`, `resolve`, `correct`, `repair`, `hotfix` | **Fixed** |
| `remove`, `delete`, `drop`, `deprecate`, `strip`, `clean` | **Removed** |
| everything else | **Changed** |

Empty categories are omitted from the output.

## Sample Output

```markdown
# Changelog

## [my-project] — Changes since v1.2.0 (2026-05-13)

### Added
- feat: add dark mode toggle (`a1b2c3d` by Jane)
- add user profile page (`e4f5g6h` by Bob)

### Fixed
- fix: resolve login redirect loop (`i7j8k9l` by Jane)

### Changed
- update dependencies to latest (`m0n1o2p` by Bot)
- refactor auth middleware (`q3r4s5t` by Bob)
```
