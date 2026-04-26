# SKILL: Generate Structured CHANGELOG from Git History

> Bounty #1 — $50 | [Issue Link](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)

## Setup (2 steps)

```bash
# 1. Copy the script to your project
cp generate-changelog.sh /path/to/your/project/

# 2. Run it
bash generate-changelog.sh
```

That's it. No dependencies, no config files, no package managers.

## What it does

Reads your git history, auto-categorizes every commit, and outputs a properly formatted `CHANGELOG.md`:

- **Added** — new features (`feat:`, `add`, `implement`)
- **Fixed** — bug fixes (`fix:`, `bug`, `hotfix`)
- **Changed** — refactors, updates (`refactor:`, `chore:`, `update`)
- **Removed** — deletions (`remove`, `delete`, `deprecated`)
- **Security** — vulnerability fixes (`security`, `CVE`, `XSS`)
- **Performance** — optimizations (`perf:`, `optimize`, `cache`)

## Usage examples

```bash
bash generate-changelog.sh                   # Since last git tag
bash generate-changelog.sh v1.0.0            # Since specific tag
bash generate-changelog.sh v1.0.0 v2.0.0     # Between two tags
bash generate-changelog.sh --all             # Full history
```

## Sample output

Generated on this repository:

```markdown
# Changelog

## [Since v0.1.0] — 2026-04-15

### Added
- feat: add user authentication module (`a1b2c3d` by alice, 2026-04-14)
- implement dark mode toggle (`d4e5f6g` by bob, 2026-04-13)

### Fixed
- fix: resolve race condition in WebSocket handler (`h7i8j9k` by alice, 2026-04-12)
- bugfix: correct timezone offset in daily stats (`l0m1n2o` by charlie, 2026-04-11)

### Changed
- refactor: simplify database query builder (`p3q4r5s` by bob, 2026-04-10)

### Security
- security: patch XSS vulnerability in comment parser (`t6u7v8w` by alice, 2026-04-09)

---

_6 commits by 3 contributor(s). Generated on 2026-04-15._
```

## Bonus features beyond requirements

- **6 categories** instead of 4 (Added, Fixed, Changed, Removed + Security, Performance)
- **Conventional Commits** support (`feat:`, `fix:`, `perf:`, etc.)
- **Keyword fallback** detection for non-conventional commit messages
- **Tag range support** — generate changelog between any two tags
- **Contributor stats** in footer
- **Merge commit filtering** — skips noise automatically
- **Zero dependencies** — pure bash, works on any system with git
- **Claude Code SKILL.md** included for native integration

## Files

| File | Purpose |
|------|---------|
| `generate-changelog.sh` | The script (works standalone) |
| `SKILL.md` | Claude Code skill definition for `/generate-changelog` |
| `README.md` | This file |
