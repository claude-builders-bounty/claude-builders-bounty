# SKILL: Generate Structured CHANGELOG from Git History

## Trigger

Use this skill when the user asks to:
- Generate a changelog
- Create a CHANGELOG.md
- Summarize recent git commits
- Run `/generate-changelog`

---

## What This Skill Does

Automatically generates a structured `CHANGELOG.md` from the project's git history by:
1. Finding the most recent git tag (baseline)
2. Fetching all commits since that tag
3. Auto-categorising them into **Added / Fixed / Changed / Removed**
4. Writing a properly formatted section to `CHANGELOG.md`

---

## Instructions for Claude

When this skill is triggered:

1. **Check that git is available and we're inside a repo:**
   ```bash
   git rev-parse --git-dir
   ```
   If not a git repo, explain that and stop.

2. **Run the changelog script:**
   ```bash
   bash changelog.sh
   ```
   Or for a preview without writing the file:
   ```bash
   bash changelog.sh --dry-run
   ```

3. **If the user wants a specific version tag:**
   ```bash
   bash changelog.sh --since v1.0.0 --version v1.1.0
   ```

4. **Show the user the output summary** (lines added per category).

5. **Offer to commit the updated file:**
   ```bash
   git add CHANGELOG.md && git commit -m "docs: update CHANGELOG for [version]"
   ```

---

## Categorisation Rules

| Prefix / keyword in commit subject | Section |
|---|---|
| `feat:`, `add`, `new`, `introduce`, `implement` | **Added** |
| `fix:`, `bug`, `patch`, `hotfix`, `resolve`, `correct` | **Fixed** |
| `refactor:`, `change`, `update`, `upgrade`, `bump`, `perf`, `style`, `chore`, `docs`, `test`, `ci` | **Changed** |
| `remove`, `delete`, `drop`, `deprecate`, `revert` | **Removed** |
| Everything else | **Changed** (safe default) |

---

## Example Output

```markdown
## [Unreleased] — 2026-03-31

### Added

- add user authentication endpoint (`a1b2c3d`)
- introduce Prometheus metrics scraping (`e4f5g6h`)

### Fixed

- fix race condition in session handler (`i7j8k9l`)
- correct null pointer in config loader (`m0n1o2p`)

### Changed

- update dependencies to latest versions (`q3r4s5t`)
- refactor database connection pooling (`u6v7w8x`)

### Removed

- remove deprecated /v1/legacy endpoint (`y9z0a1b`)
```

---

## Files

- `changelog.sh` — the main bash script (drop anywhere in the project root)
- `SKILL.md` — this file (for Claude Code)
