# Changelog Generator Skill

A Claude Code skill + zero-dependency bash script that generates a structured, Keep-a-Changelog style `CHANGELOG.md` from git history. Built for the $50 claude-builders-bounty #1.

## Setup

```
1. Copy `scripts/changelog.sh` and `skills/generate-changelog/` into your project.
2. Make it executable: `chmod +x scripts/changelog.sh`
3. Run it: `bash scripts/changelog.sh` — or `/generate-changelog` in Claude Code.
```

## What it does

- Collects commits since the last git tag (full history when there are no tags; merge commits skipped)
- Auto-categorizes into Added / Fixed / Changed / Removed via conventional-commit prefixes + keyword heuristics
- Writes a Keep-a-Changelog style `CHANGELOG.md` with one bullet per commit

## Testing

- Verified on `sharkdp/bat`: 260 commits since tag `v0.26.1`, all four categories populated — see `sample/CHANGELOG.md`.
- Verified on a scratch repo: 4 commits (feat/fix/chore/remove) each routed to the correct category.
- Requires only `git` and `bash`. No dependencies.

## Standalone

Also published as an installable Claude Code plugin: `/plugin install github:fliptrigga13/generate-changelog`
