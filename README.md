# Claude Builders Bounty

> A community bounty board for Claude Code builders.

## Active bounties

| # | Task | Amount | Status |
|---|------|--------|--------|
| [#1](../../issues/1) | Skill: generate a structured CHANGELOG from git history | $50 | Open |
| [#2](../../issues/2) | Template: CLAUDE.md for a Next.js + SQLite project | $75 | Open |
| [#3](../../issues/3) | Hook: block destructive bash commands in Claude Code | $100 | Open |
| [#4](../../issues/4) | Agent: PR reviewer with structured Markdown output | $150 | Open |
| [#5](../../issues/5) | Workflow: n8n + Claude API for weekly dev summaries | $200 | Open |

## Issue #1 deliverable

The changelog generator lives in `skills/generate-changelog/` and can be run with:

```bash
bash changelog.sh
```

It finds the latest git tag, falls back to the initial commit when no tag exists, groups commits into `Added`, `Fixed`, `Changed`, and `Removed`, and writes a deterministic `CHANGELOG.md`.

## Setup

1. Copy `skills/generate-changelog` into your Claude skills directory.
2. Run `bash changelog.sh` from a git repo.
3. Commit the generated `CHANGELOG.md`.

## Sample

See `skills/generate-changelog/examples/sample-CHANGELOG.md` for output generated from this repo's public git history.
