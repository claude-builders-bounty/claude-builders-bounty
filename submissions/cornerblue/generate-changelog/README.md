# generate-changelog ($50 bounty skill)

Bash + Claude Code skill that writes a structured `CHANGELOG.md` from git history since the last tag.

## Setup (≤3 steps)

1. Copy into Claude skills (or keep the script only):

```bash
mkdir -p ~/.claude/skills/generate-changelog
cp SKILL.md changelog.sh ~/.claude/skills/generate-changelog/
chmod +x ~/.claude/skills/generate-changelog/changelog.sh
```

2. From any git repo, generate:

```bash
bash ~/.claude/skills/generate-changelog/changelog.sh CHANGELOG.md
```

3. Or in Claude Code: ask to `/generate-changelog` (skill description matches).

## Acceptance

- [x] Works via skill or `bash changelog.sh`
- [x] Commits since last tag
- [x] Added / Fixed / Changed / Removed
- [x] Writes `CHANGELOG.md`
- [x] Sample output included (`sample/CHANGELOG.md`)
- [x] README ≤3 steps

## Author

@cornerblue — BTC `bc1qjtevjy8gldfhkra6n5g4yclpr5uafyd7k0j2ls`
