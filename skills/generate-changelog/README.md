# generate-changelog

> Bash script and Claude Code skill that builds a structured `CHANGELOG.md` from git commit history.

Bounty submission for [issue #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1).

## Quick start

1. `chmod +x skills/generate-changelog/changelog.sh`
2. `bash skills/generate-changelog/changelog.sh` (or `bash changelog.sh` from this directory)
3. Open the generated `CHANGELOG.md`

Sample output from this repo: [`samples/CHANGELOG.sample.md`](samples/CHANGELOG.sample.md).

## Claude Code

Copy this folder to `.claude/skills/generate-changelog/` to enable the `/generate-changelog` command.

## Tests

```bash
bash skills/generate-changelog/tests/test_changelog.sh
```
