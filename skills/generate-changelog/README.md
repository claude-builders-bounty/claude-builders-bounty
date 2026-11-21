# Structured Git Changelog Generator (`/generate-changelog` & `changelog.sh`)

Automatically generates a structured `CHANGELOG.md` from git commit history since the latest git tag, categorized into **Added**, **Fixed**, **Changed**, and **Removed**.

## Quick Setup (3 Steps)

1. Copy `changelog.sh` and `SKILL.md` (`.claude/skills/generate-changelog/SKILL.md`) into your project and mark executable:
   ```bash
   chmod +x changelog.sh
   ```
2. Generate `CHANGELOG.md` from bash or inside Claude Code via `/generate-changelog`:
   ```bash
   bash changelog.sh
   ```
3. Review the generated `CHANGELOG.md` in your project root.

## Tested Sample Output (`colinhacks/zod`, `v4.6.7..HEAD`)

See [`SAMPLE_CHANGELOG.md`](./SAMPLE_CHANGELOG.md) for the full output generated directly by `bash changelog.sh` against `github.com/colinhacks/zod`.
