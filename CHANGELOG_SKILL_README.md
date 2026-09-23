# generate-changelog — setup & usage

A Claude Code skill + stdlib-only Python script that builds a
structured `CHANGELOG.md` from git history, auto-categorized into
`Added` / `Fixed` / `Changed` / `Removed`.

## Setup (3 steps)

1. **Copy the files into your project** (or this repo already has
   them): `SKILL.md`, `scripts/generate_changelog.py`.
2. **Require Python 3** — nothing else. The script is single-file,
   stdlib-only, no pip install.
3. **Run it:**
   ```bash
   python3 scripts/generate_changelog.py          # writes ./CHANGELOG.md
   python3 scripts/generate_changelog.py NOTES.md # writes another file
   ```
   In Claude Code you can also just ask for `/generate-changelog`
   (the skill entry is `SKILL.md`).

That's the whole setup.

## How it works

- Finds the most recent tag with `git describe --tags --abbrev=0`;
  if the repo has no tags it uses all commits on HEAD and today's
  date as the section heading.
- Categorizes each commit subject by conventional-commit keywords:
  - **Added** — `feat`, `feature`, `add`, `new`, `support`
  - **Fixed** — `fix`, `bugfix`, `patch`, `hotfix`
  - **Changed** — `change`, `update`, `refactor`, `improve`, `chore`,
    `perf`, `doc`, `test`, `style`, and anything unrecognized
  - **Removed** — `remov*`, `deprecat*`, `delete`, `drop`, `breaking`
- Strips the conventional prefix so entries read naturally
  (`feat: add login` → `Add login`) and appends the short hash.
- Prepends a new `## <version> (<date>)` block to an existing
  `CHANGELOG.md` (or creates one with a `# Changelog` header).

## Sample output

Tagged repo (last tag `v1.1.0`, two commits after it):

```markdown
# Changelog

## v1.1.0 (2026-09-21)
### Added
- Support OAuth2 (`1bb882d`)

### Fixed
- Handle null user (`a7a91a4`)
```

Repo with **no** tags (all history, date placeholder):

```markdown
# Changelog

## 2026.09.21 (2026-09-21)
### Added
- Initial feature (`b337d6f`)

### Fixed
- Bug (`0df94fe`)
```

Both outputs are reproduced in `test_fixtures/` (tagged + untagged
demo repos) so you can diff them without running anything.

## Notes

- Categorization is keyword-driven (conventional commits), so
  `feat:`/`fix:` style subjects are the most reliable; plain-English
  subjects fall back to `Changed`.
- Re-running after new commits prepends a new version block; the
  version heading reuses the last tag when none is created in between.
