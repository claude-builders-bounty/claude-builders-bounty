# changelog-generator

Generate a structured `CHANGELOG.md` from your git history — categorised into
**Added / Changed / Fixed / Removed** ([Keep a Changelog](https://keepachangelog.com/)
format). Works as a plain bash script and as a Claude Code slash command.

## Setup (3 steps)

1. Copy the script into your repo (or anywhere on PATH):
   ```bash
   cp skills/changelog-generator/changelog.sh .
   ```
2. Make it executable:
   ```bash
   chmod +x changelog.sh
   ```
3. Run it:
   ```bash
   bash changelog.sh -o CHANGELOG.md
   ```

### Optional: use as a Claude Code command
Copy `generate-changelog.md` to `~/.claude/commands/` (or `.claude/commands/`
in your project); then `/generate-changelog` runs the script for you.

## Usage

```bash
bash changelog.sh                 # print to stdout
bash changelog.sh -o CHANGELOG.md # write (prepends a new block if file exists)
bash changelog.sh --since v1.2.0  # explicit starting ref
bash changelog.sh --version 1.3.0 # set the version header
```

- Commits are collected **since the most recent git tag** (or full history if
  there are no tags), merges excluded.
- Categorisation uses Conventional-Commit prefixes first
  (`feat:` → Added, `fix:` → Fixed, `refactor:`/`perf:`/`docs:`/`chore:` →
  Changed, `remove:`/`revert:` → Removed), then keyword heuristics for
  non-conventional messages.

## Sample output

Given commits since `v1.0.0`:

```
feat: add user login
fix: correct null pointer
refactor: simplify auth
remove: drop legacy API
Add dark mode toggle
```

`bash changelog.sh --version 1.1.0` produces:

```markdown
# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/), categories
derived from git history (since v1.0.0).

## [1.1.0] - 2026-09-22

### Added

- Add dark mode toggle
- Add user login

### Changed

- Simplify auth

### Fixed

- Correct null pointer

### Removed

- Drop legacy API
```
