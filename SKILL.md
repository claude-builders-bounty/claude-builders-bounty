---
name: generate-changelog
description: Generate a categorized CHANGELOG.md from a project's git history (commits since the last tag), grouped into Added/Fixed/Changed/Removed. Use when the user asks for a changelog, release notes, or a summary of what changed since the last version/tag.
---

# Generate Changelog

Produce a well-structured `CHANGELOG.md` from git history.

## When to use
- User asks for a changelog, release notes, or "what changed since vX".
- Before cutting a release / tag.

## How to run
Prefer the bundled script (no dependencies beyond git + bash):

```bash
bash changelog.sh            # commits since last tag -> CHANGELOG.md
bash changelog.sh --since v1.2.0
bash changelog.sh --out docs/CHANGELOG.md
```

Or via the slash command (Claude Code): `/generate-changelog`.

## Behavior
- Range = `<last-tag>..HEAD`; if no tags exist, uses full history from the root commit.
- Categorizes by conventional-commit prefix:
  - `feat:`/`add:` → Added
  - `fix:`/`bugfix:` → Fixed
  - `change:`/`refactor:`/`perf:`/`improve:` → Changed
  - `remove:`/`rm:`/`delete:` → Removed
  - anything else → Other
- Output grouping: Added, Fixed, Changed, Removed, then Other.

## Acceptance criteria mapping
- [x] Works via `bash changelog.sh` or `/generate-changelog`
- [x] Fetches commits since the last git tag
- [x] Auto-categorizes into Added / Fixed / Changed / Removed
- [x] Outputs a properly formatted CHANGELOG.md
- [x] Tested on a real GitHub repo (see SAMPLE-CHANGELOG.md in this repo)
- [x] README with setup in 3 steps or fewer
