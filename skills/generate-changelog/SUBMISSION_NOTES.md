# Submission Notes for Bounty #1

Issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1

## PR Title
`feat: skill and script to generate structured CHANGELOG from git history`

## PR Description

Closes #1

### Summary
This PR implements a Claude Code skill and zero-dependency bash/Python script that automatically parses git history and generates a structured `CHANGELOG.md` adhering to the [Keep a Changelog](https://keepachangelog.com/) standard.

### Acceptance Criteria Checklist
- [x] **Works via `/generate-changelog` command or `bash changelog.sh`**
  - Native Claude Code skill defined in `skills/generate-changelog/SKILL.md` (and `.claude/skills/generate-changelog/SKILL.md`).
  - Standalone executable runner `changelog.sh` at repository root.
- [x] **Fetches commits since the last git tag**
  - Automatically discovers the latest tag via `git describe --tags --abbrev=0`.
  - Supports `--since-tag <tag>` and `--all` flags.
- [x] **Auto-categorizes into `Added` / `Fixed` / `Changed` / `Removed`**
  - Matches conventional commit prefixes (`feat:`, `fix:`, `refactor:`, `remove:`, etc.) and natural verbs.
- [x] **Outputs a properly formatted `CHANGELOG.md`**
  - Follows Keep a Changelog with `[Unreleased]` or custom version titles and dates.
  - Supports `--prepend` to preserve existing release history.
- [x] **Tested on a real GitHub repo**
  - Sample output included in `samples/CHANGELOG-sample.md`.
- [x] **README with setup instructions in 3 steps or fewer**
  - Documented in `skills/generate-changelog/README.md`.

### Verification
```bash
python3 skills/generate-changelog/test_changelog.py
bash changelog.sh --stdout
```
All automated tests pass.
