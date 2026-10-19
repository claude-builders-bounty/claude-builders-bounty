# Claude Builders Bounty — Structured Git Changelog Skill (`#1`)

Automated `CHANGELOG.md` generator from git history (supports both `bash changelog.sh` and Claude Code `/generate-changelog` via `SKILL.md`).

## Quick Setup (3 Steps)
1. **Clone & Make Executable:**
   ```bash
   chmod +x changelog.sh
   ```
2. **Generate `CHANGELOG.md` for Any Git Repo:**
   ```bash
   bash changelog.sh CHANGELOG.md /path/to/repo
   ```
3. **Or Use in Claude Code:**
   Copy `SKILL.md` into `.claude/skills/generate-changelog/SKILL.md` and run `/generate-changelog`.

## Sample Output (Tested on Live GitHub Repo `ryder777777/darwin-omega-wealth-swarm`)
See [`SAMPLE_CHANGELOG.md`](./SAMPLE_CHANGELOG.md) for real generated output.
