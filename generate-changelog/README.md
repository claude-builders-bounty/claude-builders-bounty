# generate-changelog

A Claude Code skill + bash script that turns git history into a structured
`CHANGELOG.md` — commits since the last tag, auto-categorized into
**Added / Fixed / Changed / Removed**, Keep a Changelog style.

## Setup (3 steps)

1. Copy this `generate-changelog/` folder into your project root.
2. *(Claude Code only — enables `/generate-changelog`)* install skill and command:

   ```bash
   mkdir -p .claude/skills/generate-changelog .claude/commands
   cp generate-changelog/SKILL.md .claude/skills/generate-changelog/SKILL.md
   cp generate-changelog/commands/generate-changelog.md .claude/commands/
   ```

3. From the repo root, run:

   ```bash
   bash generate-changelog/changelog.sh        # writes ./CHANGELOG.md
   ```

Plain bash (no Claude Code) works too — step 2 is optional and step 3 is all you need.

## Usage

```
changelog.sh [-o OUTPUT] [--since REF | --no-tag] [-f] [REPO_DIR]
```

- Fetches commits since the newest tag (`git describe --tags --abbrev=0`); if the
  repo has no tags, the full history is used. `--since REF` overrides the cutoff.
- Categorization: conventional-commit prefixes first (`feat:` → Added, `fix:` →
  Fixed, `revert:` → Removed), then keyword heuristics on the subject
  (add/support → Added, bug/crash → Fixed, remove/drop/deprecate → Removed);
  everything else lands in Changed.
- A hand-written `CHANGELOG.md` is never clobbered — the script refuses unless it
  contains its own `generated-by` marker or you pass `-f`.
- In Claude Code, `/generate-changelog` runs the script and then has Claude
  re-verify categorization against the actual diffs (`SKILL.md` steps 2–4).

## Tests

```bash
bash generate-changelog/test_changelog.sh   # builds a throwaway git repo, asserts everything
```
