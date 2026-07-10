# generate-changelog

Generate a structured `CHANGELOG.md` from git history since the last tag. Categories: **Added**, **Fixed**, **Changed**, **Removed**.

## Setup (3 steps)

1. Copy this folder into your project (or into `~/.claude/skills/generate-changelog` for Claude Code).
2. Make the script executable: `chmod +x generate-changelog/changelog.sh`
3. Run it:

```bash
bash generate-changelog/changelog.sh
# Claude Code: /generate-changelog
```

Optional: write to a custom path — `bash generate-changelog/changelog.sh docs/CHANGELOG.md`.

## Sample output

Tested on [claude-builders-bounty/claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty) (no tags; full history):

```markdown
# Changelog

All notable changes to this project are documented in this file.

Generated from git history
(full history; no tags found).

## [Unreleased]

### Added
- Initial README with bounty board
```

See `sample-CHANGELOG.md` for the file written by the script.
