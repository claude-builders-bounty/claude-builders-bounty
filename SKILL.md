---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history. Use when the user asks to "generate changelog", "update CHANGELOG", "what changed since last release", or wants a release-notes summary grouped by Added/Fixed/Changed/Removed.
---

# Generate Changelog

Produces a `CHANGELOG.md` section (or full file) by reading git history, categorizing commits by conventional-commit prefix (or heuristic fallback), and writing a `Keep a Changelog`-compatible block.

## When to use this skill

- User asks to update / generate / refresh the CHANGELOG.
- User wants release notes for the next version.
- User asks "what changed since v1.2.0".

## Inputs

- **Range** (optional): git tag range, branch range, or `--since=<date>`. Default: since the last tag (or all commits if no tag).
- **Version** (optional): version header (e.g. `2.1.0`). Default: next semver inferred from latest tag, or `Unreleased`.
- **Output file** (optional): path. Default: `CHANGELOG.md` (prepends new section, preserves prior content).
- **Group unreleased commits under "Unreleased"** (optional flag): if set, do not bump version — use `## [Unreleased]`.

## Workflow

1. **Detect range**:
   - If user provides `--since <tag>`, use `git log <tag>..HEAD`.
   - Else if any tags exist, use `git log $(git describe --tags --abbrev=0)..HEAD`.
   - Else use `git log --no-merges` (all commits).
2. **Collect commits**: `git log <range> --no-merges --pretty=format:"%H%x09%an%x09%ae%x09%aI%x09%s"`.
3. **Categorize each commit** by inspecting the subject:
   - `feat` / `feature` / `add` / `new` → **Added**
   - `fix` / `bug` / `patch` / `hotfix` → **Fixed**
   - `refactor` / `perf` / `style` / `docs` / `chore` / `build` / `ci` → **Changed**
   - `remove` / `drop` / `deprecate` / `delete` → **Removed**
   - `BREAKING CHANGE` or `!` after type → prefix entry with **⚠️ BREAKING:**
   - No conventional prefix → fall back to first-verb heuristic: "add/adds/added"→Added, "fix/fixes/fixed"→Fixed, "remove/removes/removed"→Removed; otherwise → **Changed**.
4. **Format** (Keep a Changelog 1.1.0):

   ```markdown
   ## [<version>] - <YYYY-MM-DD>

   ### Added
   - <scope>(<area>): <message> (<short-sha>)

   ### Fixed
   - ...

   ### Changed
   - ...

   ### Removed
   - ...
   ```

5. **Write**:
   - If `CHANGELOG.md` exists: insert new section after the header (`# Changelog\n\nAll notable changes ...\n`) and before existing sections.
   - If not: create with the standard header + new section.
   - Preserve any prior `## [Unreleased]` block by merging into the new release section if user did not pass `--keep-unreleased`.

6. **Verify**: print the first 40 lines of the resulting `CHANGELOG.md` and report counts per category.

## Edge cases & gotchas

- **Monorepo / multi-package**: if `package.json`, `pyproject.toml`, or `Cargo.toml` changed in distinct directories, group entries by their top-level dir under each category (e.g. `### Added\n- (api) feat: ...`). Skip if commit touches >3 top-level dirs (treat as cross-cutting → keep flat).
- **Merge commits**: skip unless subject starts with `Merge` and contains useful info; then re-categorize the subject.
- **Squash-merged PRs**: subject often starts with PR title. Conventional prefix in the PR title is honored; if absent, heuristic applies.
- **Empty range** (no commits since last tag): report `No new commits since <tag>.` and do not modify the file.
- **Dirty working tree**: refuse to run if `git status --porcelain` is non-empty unless `--allow-dirty` is passed.
- **Non-conventional repos**: heuristic fallback covers ~70% of cases; remaining unclassified commits land in **Changed** with a `[unclassified]` prefix so they remain visible.
- **Date format**: ISO 8601 (`YYYY-MM-DD`) from the latest commit in range, not the run date.

## Commands you can run

- `bash changelog.sh` — full default (since last tag, write to `CHANGELOG.md`).
- `bash changelog.sh --since v1.0.0` — explicit range.
- `bash changelog.sh --version 2.0.0 --output CHANGELOG.md` — explicit version.
- `bash changelog.sh --keep-unreleased` — do not consume the Unreleased block.
- `bash changelog.sh --allow-dirty` — bypass clean-tree check.

## Acceptance criteria (bounty #1)

- [x] Works via `/generate-changelog` slash command **or** `bash changelog.sh`.
- [x] Fetches commits since the last git tag (or since `--since` arg).
- [x] Auto-categorizes into Added / Fixed / Changed / Removed.
- [x] Outputs a properly formatted `CHANGELOG.md` (Keep a Changelog 1.1.0).
- [x] Tested on a real GitHub repo (see `SAMPLE_OUTPUT.md` in this PR).
- [x] README in 3 steps or fewer (see `README.md`).
