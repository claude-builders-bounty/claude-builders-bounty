# /generate-changelog — CHANGELOG.md from git history

Generate a structured `CHANGELOG.md` from your git history, auto-categorized into
**Added / Fixed / Changed / Removed** using conventional-commit and keyword heuristics.

## Setup (3 steps)

1. Copy `changelog.sh` and `SKILL.md` into your repo (skill goes to `.claude/skills/generate-changelog/SKILL.md`).
2. `chmod +x changelog.sh`
3. Run `bash changelog.sh` (or invoke `/generate-changelog` in Claude Code). Done.

## Usage

```bash
bash changelog.sh            # Unreleased section since last git tag -> CHANGELOG.md
bash changelog.sh --all      # One section per tag + Unreleased
bash changelog.sh --stdout   # Print instead of overwriting CHANGELOG.md
```

- Commits since the **most recent tag** are the default scope.
- `feat:`/`add…` → **Added**, `fix:`/`revert…` → **Fixed**, `remove…/deprecat…` → **Removed**,
  everything else → **Changed**. Merge commits and release-churn commits are skipped.
- Category headings follow [Keep a Changelog](https://keepachangelog.com/) so the output
  drops straight into existing release processes.

## Tested on

Tested against the public repo `github.com/sindresorhus/is-identifier` and against a
synthetic repo with `feat:`/`fix:`/`remove:` history; sample output in `sample-output.md`.
Zero dependencies beyond `bash`, `git`, `grep`, `sed`, `coreutils` (available on any
Linux/macOS CI image).
