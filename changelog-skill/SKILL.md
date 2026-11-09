---
name: generate-changelog
description: Generate a structured CHANGELOG.md section from a project's git history since the last git tag, auto-categorized into Added / Fixed / Changed / Removed in Keep a Changelog format. Use when the user asks to generate or update a changelog, draft release notes, summarize changes since the last release, or runs /generate-changelog.
---

# Generate Changelog

Generate a structured changelog section from git history with the bundled
deterministic script — do not hand-write the categorization.

## Steps

1. Make sure you are inside the target git repository (or note its path).
2. Run the generator. It collects commits since the last git tag, splits
   them into `Added` / `Fixed` / `Changed` / `Removed`, and formats a
   Keep a Changelog section:

   ```bash
   bash <skill-dir>/changelog.sh --prepend CHANGELOG.md
   ```

   Useful options:

   - `--version 1.4.0 --date 2026-11-09` — title the section with a real
     version and release date instead of `Unreleased`.
   - `--tag v1.2.0 --to v1.3.0` — generate for an explicit range (e.g.
     documenting an already-shipped release).
   - `--repo /path/to/repo` — run against a repo other than the cwd.
   - No `--prepend` — the section is printed to stdout for review first.

3. Show the user the generated section. Sanity-check the categorization:
   the script maps Conventional Commits types (`feat` → Added, `fix` →
   Fixed, everything else → Changed), treats a leading remove/delete/drop
   verb as Removed, and files pure-deletion commits under Removed. Flag
   anything that looks miscategorized rather than silently editing it.
4. If the user wants different wording for an entry, edit the entry in
   `CHANGELOG.md` directly — never re-run the script over manual edits
   without warning, because `--prepend` inserts a fresh section.

## Notes

- Requires `git` and `python3` (standard library only, no pip installs).
- Merge commits are excluded; the section is based on the commits that
  actually landed.
- A repo with no tags is handled: all commits up to HEAD are used.
