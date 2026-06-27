# Skill: Generate Changelog

## Trigger
`/generate-changelog`

## What this skill does

Generates a structured `CHANGELOG.md` from the current repository's git history, following the [Keep a Changelog](https://keepachangelog.com) format.

## Steps

1. **Find the starting point**: detect the last git tag (or use `--since TAG`) as the baseline. If no tags exist, include all commits.

2. **Collect commits**: run `git log <tag>..HEAD` to get all commits since the baseline. Extract SHA, subject line, and body.

3. **Categorize each commit** by conventional commit prefix or keywords:
   - `feat` / `add` / `new` → **Added**
   - `fix` / `bug` → **Fixed**
   - `refactor` / `update` / `chore` → **Changed**
   - `remove` / `delete` / `drop` → **Removed**
   - `docs` → **Docs**
   - anything else → **Changed**

4. **Generate Markdown** in Keep a Changelog format with dated version header.

5. **Write** to `CHANGELOG.md` in the repo root.

## Usage

**Using the Python script:**
```bash
python changelog.py                 # auto-detect last tag
python changelog.py --since v1.2   # from specific tag
python changelog.py --days 14      # last 14 days
python changelog.py --output -     # preview to stdout
python changelog.py --dry-run      # preview without writing
```

**Using the bash wrapper:**
```bash
bash changelog.sh                  # auto-detect last tag
bash changelog.sh v1.2             # from specific tag
```

## Example output

```markdown
# Changelog

All notable changes to **myproject** are documented here.

---

## [Unreleased] — 2026-06-27
_Changes since v1.2.0_

### Added

- add OAuth2 login support (a1b2c3d)
- add rate limiting to API endpoints (e4f5g6h)

### Fixed

- handle null pointer when session expires (i7j8k9l)

### Changed

- refactor authentication middleware (m1n2o3p)

### Docs

- update API reference with new endpoints (q4r5s6t)
```

## When invoked via `/generate-changelog`

Run the skill by telling Claude Code to follow these steps in the current repo. Claude will:
1. Run `git tag --sort=-version:refname` to find the latest tag
2. Run `git log <tag>..HEAD --pretty=format:"%H %s"` to collect commits
3. Categorize each commit
4. Output `CHANGELOG.md`

Alternatively, use the Python script directly: `python changelog.py`
