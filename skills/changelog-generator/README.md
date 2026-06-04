# ChangeLog Generator — README

A Claude Code / Hermes skill that generates structured CHANGELOG.md from git history.

## Setup (3 steps)

1. **Place the files** — Copy `changelog.sh` and `SKILL.md` to your project root
2. **Make executable** — `chmod +x changelog.sh`
3. **Run it** — `bash changelog.sh`

Or install as a Hermes skill:
```bash
mkdir -p ~/.hermes/skills/generate-changelog/
cp changelog.sh ~/.hermes/skills/generate-changelog/
cp SKILL.md ~/.hermes/skills/generate-changelog/
```

## Sample Output (tested on this repo)

See [sample-output.md](./sample-output.md)

## Files
- `changelog.sh` — The generator script
- `SKILL.md` — Hermes/Claude Code skill definition

Bounty: $50 — https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1
Wallet: 0x53b0957b9d7c86c6c20463e945044cd722227728
