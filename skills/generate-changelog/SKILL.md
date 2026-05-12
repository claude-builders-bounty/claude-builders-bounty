# Generate Changelog

Generate a structured `CHANGELOG.md` from git history following [Keep a Changelog](https://keepachangelog.com/) format.

## Trigger

When the user says `/generate-changelog`, "generate a changelog", "update the changelog", or asks to produce release notes from git history.

## Steps

1. **Find the last tag** — Run `git describe --tags --abbrev=0 2>/dev/null` to get the most recent tag. If no tags exist, use the first commit (`git rev-list --max-parents=0 HEAD`).

2. **Collect commits** — Run:
   ```bash
   git log ${LAST_TAG}..HEAD --pretty=format:"%H|%s|%an" --no-merges
   ```
   If no last tag, run against all commits:
   ```bash
   git log --pretty=format:"%H|%s|%an" --no-merges
   ```

3. **Categorize each commit** by parsing the subject line prefix (case-insensitive):

   | Prefix | Category |
   |--------|----------|
   | `feat:`, `feature:`, `add:` | **Added** |
   | `fix:`, `bugfix:`, `patch:` | **Fixed** |
   | `refactor:`, `change:`, `update:`, `chore:`, `docs:`, `test:`, `ci:`, `build:`, `perf:` | **Changed** |
   | `deprecate:` | **Deprecated** |
   | `remove:`, `delete:` | **Removed** |
   | `security:` | **Security** |
   | No recognized prefix | **Changed** (fallback) |

   Also handle non-prefixed conventional verbs (e.g., "Add feature", "Fix bug", "Remove old code").

4. **Build the changelog** — Write in Keep-a-Changelog format:
   ```markdown
   # Changelog

   ## [Unreleased]

   ### Added
   - feat: add user authentication (#123) by @author

   ### Fixed
   - fix: resolve login redirect loop (#122) by @author

   ### Changed
   - refactor: simplify config loading (#121) by @author

   ### Deprecated
   - deprecate: old-style config format (#119) by @author

   ### Removed
   - remove: legacy API v1 endpoints (#120) by @author

   ### Security
   - security: patch dependency vulnerability (#118) by @author
   ```

5. **If `CHANGELOG.md` already exists** — Prepend the new entries under a new `[Unreleased]` heading. Do not delete existing entries.

6. **Show the result** — Print the generated section to the user and confirm the file was written.

## Constraints

- Only read git history; do not modify commits or tags.
- Skip merge commits (`--no-merges`).
- If a commit references a PR number (`#123`), include it as-is from the subject line.
- Keep entries as one-liners (subject line only, no body).
- Sort entries within each category by commit date (newest first).
- A standalone bash script (`generate-changelog.sh`) is also provided for use outside Claude Code.
