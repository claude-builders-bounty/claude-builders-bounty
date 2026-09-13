# generate-changelog — Keep a Changelog from git history

**Bounty:** [#1 — $50](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)  
**Author:** KvngJamesII

Bash + Claude Code skill that turns commits since the last git tag into a Keep a Changelog `CHANGELOG.md` (`Added` / `Fixed` / `Changed` / `Removed`).

## Setup (3 steps)

1. Copy this folder into your project (or into `~/.claude/skills/generate-changelog/`).
2. From any git repo: `bash path/to/changelog.sh`
3. Open the generated `CHANGELOG.md` (or preview with `bash path/to/changelog.sh --stdout`).

Optional Claude Code: place `SKILL.md` + `changelog.sh` under `~/.claude/skills/generate-changelog/` and run `/generate-changelog`.

## Demo

Sample output (real repo `cli/cli`, range `v2.74.0..HEAD`) is in [`sample-output.md`](./sample-output.md).
