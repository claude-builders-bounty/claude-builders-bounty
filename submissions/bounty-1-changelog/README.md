# CHANGELOG Generator — Bounty #1

Structured `CHANGELOG.md` generator for Claude Code projects.

## Setup (3 steps)

1. Copy the skill and script into your Claude skills directory:

```bash
mkdir -p ~/.claude/skills/generate-changelog/scripts
cp SKILL.md ~/.claude/skills/generate-changelog/
cp scripts/changelog.sh ~/.claude/skills/generate-changelog/scripts/
chmod +x ~/.claude/skills/generate-changelog/scripts/changelog.sh
```

2. Run from any git repo:

```bash
bash ~/.claude/skills/generate-changelog/scripts/changelog.sh
```

3. Or invoke via Claude Code: `/generate-changelog`

## What it does

- Fetches commits since the last git tag (`git describe --tags --abbrev=0`)
- Auto-categorizes into **Added / Fixed / Changed / Removed**
- Writes Keep-a-Changelog-style markdown
- Zero dependencies beyond git and bash

## Sample output

See [`samples/CHANGELOG-sample.md`](samples/CHANGELOG-sample.md) — generated from this bounty repo.

## Testing

```bash
./scripts/changelog.sh /tmp/CHANGELOG.md .
cat /tmp/CHANGELOG.md
```