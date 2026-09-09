# changelog-skill

Generate a structured `CHANGELOG.md` (Added / Fixed / Changed / Removed) from git history — as a native Claude Code skill (`/generate-changelog`) or a standalone bash script.

## Setup (3 steps)

1. **Install the skill** — copy `changelog-skill/` into your Claude Code project's `.claude/skills/` directory (or keep it anywhere and use the script directly):

   ```bash
   cp -r changelog-skill .claude/skills/changelog-skill
   ```

2. **Run it** — from your repository root:

   ```bash
   # via the script
   bash changelog-skill/changelog.sh

   # or via Claude Code
   /generate-changelog
   ```

3. **Review** — `CHANGELOG.md` is written to the repo root with commits since your last git tag, auto-categorized. Empty sections are omitted.

## How it works

- Reads commits since `git describe --tags --abbrev=0` (falls back to full history when the repo has no tags)
- Categorizes each commit subject by conventional-commit prefix with keyword fallbacks:
  - `feat|add|new|introduce` → **Added**
  - `fix|bug|patch|repair|correct` → **Fixed**
  - `revert|remove|delete|drop` → **Removed**
  - everything else → **Changed**
- Skips merge commits and outputs only non-empty sections

See `sample/CHANGELOG.md` for real output generated on a live repository.
