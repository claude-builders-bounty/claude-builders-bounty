# changelog skill

Generates a Keep a Changelog-formatted `CHANGELOG.md` entry from git history —
commits since the last tag, auto-categorized into Added / Changed / Removed /
Fixed / Internal.

## Setup (3 steps)

```bash
# 1. copy the skill into your project
mkdir -p .claude/skills && cp -r skills/changelog .claude/skills/

# 2. in Claude Code, run:
#    /generate-changelog           (or: "use the changelog skill")

# 3. commit the result
git add CHANGELOG.md && git commit -m "docs: changelog for <version>"
```

## What it does

- Finds the last git tag (`git describe --tags --abbrev=0`) as the range start
- Classifies each commit by intent — merge commits are skipped, branch work is
  credited by its own commit subjects
- Omits empty sections; refuses to fabricate an entry when the range is empty
- Prepends to an existing CHANGELOG.md, preserving its header

## Sample

See `examples/sample-output.md` — generated against a real repository
(25 commits, mixed features/fixes/merges).
