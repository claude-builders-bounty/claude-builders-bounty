# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from a project's git history.

## What It Does

Parses git commits since the last tag (or all commits if no tags exist), categorizes them, and outputs a formatted CHANGELOG.md.

## Usage

### Option 1: Bash Script

```bash
bash changelog.sh [options]
```

Options:
- `-o FILE` — Output file (default: `CHANGELOG.md`)
- `-t TAG` — Generate since this tag (auto-detected if omitted)
- `-r REPO` — Path to git repo (default: current directory)
- `-a` — Include all commits (not just since last tag)

### Option 2: Claude Code Command

Ask Claude: *"Generate a changelog from git history"*

Claude will run the script and produce the changelog inline or write it to a file.

## Commit Convention

Commits are categorized by prefix keywords:

| Category | Triggers |
|----------|----------|
| **Added** | `feat`, `add`, `new`, `implement` |
| **Fixed** | `fix`, `bug`, `patch`, `resolve`, `close` |
| **Changed** | `change`, `update`, `refactor`, `improve`, `modify`, `chore`, `perf` |
| **Removed** | `remove`, `delete`, `deprecate`, `drop` |

Commits without a recognized prefix go into **Other Changes**.

## Example Output

```markdown
# Changelog

## [1.2.0] — 2026-03-27

### Added
- feat: add OAuth2 login support (a1b2c3d)
- feat: implement webhook retry logic (e4f5g6h)

### Fixed
- fix: resolve null pointer in auth middleware (i7j8k9l)

### Changed
- refactor: simplify database connection pool (m0n1o2p)

### Removed
- remove: drop legacy XML export endpoint (q3r4s5t)
```
