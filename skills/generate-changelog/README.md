# changelog-generator

Generate a structured `CHANGELOG.md` from git history. Commits since the last
git tag are auto-categorized into **Added / Fixed / Changed / Removed** and
rendered in Keep-a-Changelog style.

## Setup (3 steps)

1. Copy `changelog.py` and `changelog.sh` into your project (or anywhere on `PATH`).
2. Make the wrapper executable: `chmod +x changelog.sh` (needs Python 3, no extra packages).
3. Run it: `bash changelog.sh --repo /path/to/your/repo`

That's it — `CHANGELOG.md` appears in the current directory. As a Claude Code
skill, drop `SKILL.md` into your skills folder and invoke `/generate-changelog`.

## Options

| Flag | Effect |
|------|--------|
| `--stdout` | Print markdown instead of writing `CHANGELOG.md` |
| `--since v1.2.0` | Start from a specific tag instead of the latest tag |
| `--output NOTES.md` | Write to a different file |
| `--repo DIR` | Target repository (default: current directory) |

## Sample output

Tested on a local repo with 6 categorized commits, and on the real public repo
typicode/husky (last tag v9.1.7). Sample from local test:

```markdown
# Changelog

## [Unreleased (since v0.1.0)] - auto-generated from git history

### Added

- Add dark mode toggle (8b72e2e)
- feat(api): introduce webhook endpoint (70c2458)

### Fixed

- fix(auth): resolve token refresh race (cf00368)

### Changed

- docs: rewrite README setup section (3e35c52)
- refactor: simplify retry logic (f8664f0)

### Removed

- remove: drop legacy json export flag (90126d4)
```
