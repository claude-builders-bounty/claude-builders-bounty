---
name: generate-changelog
description: Generate a Keep-a-Changelog style CHANGELOG.md from git history since the last tag. Auto-categorizes commits into Added / Fixed / Changed / Removed using Conventional Commits prefixes and keyword heuristics. Use when the user runs /generate-changelog or asks to summarize recent commits, build a release CHANGELOG, or update CHANGELOG.md for a new version.
---

# generate-changelog

When the user invokes `/generate-changelog` or asks for a CHANGELOG, run the bash script that ships next to this skill:

```bash
bash changelog.sh > CHANGELOG.md
```

Optional flags:

- `--since <tag>` — start point (default: `git describe --tags --abbrev=0`)
- `--next-version <ver>` — version label for the new section (default: auto-bump patch of last tag, or `Unreleased`)

After the script runs:

1. `Read` the generated `CHANGELOG.md` and show the user the categorized list.
2. Ask if they want any edits (e.g. merging dupes, expanding cryptic subjects).
3. If approved, suggest committing with `git add CHANGELOG.md && git commit -m "docs: update CHANGELOG for <version>"`.
4. Suggest tagging with `git tag <version> && git push --tags` if the user agrees.

## How categorization works

Each commit subject is classified by:

1. **Conventional Commits prefix** (highest priority):
   - `feat:` / `feat(scope):` → **Added**
   - `fix:` / `hotfix:` / `bugfix:` → **Fixed**
   - `chore:` / `refactor:` / `perf:` / `style:` / `docs:` / `test:` / `ci:` / `build:` / `revert:` → **Changed**
   - `remove:` / `drop:` / `deprecate:` → **Removed**

2. **Keyword fallback** (if no Conventional prefix):
   - add / new / implement / support → **Added**
   - fix / bug / patch / resolve → **Fixed**
   - update / change / modify / refactor / improve / bump → **Changed**
   - remove / delete / deprecate / drop → **Removed**

3. Anything else lands in **Other**.

## Edge cases the script handles

- No prior tag: includes the full history with an "all commits" note.
- Empty range (HEAD == last tag): produces a section with no bullets.
- Merge commits are skipped (`--no-merges`) to keep the changelog clean.
- Commit subjects with backticks / pipes are preserved verbatim.
