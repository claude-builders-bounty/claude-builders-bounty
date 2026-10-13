# SKILL: Generate a structured CHANGELOG from git history

A Claude Code skill that turns raw `git log` output into a structured,
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/)-compliant `CHANGELOG.md`,
grouping commits by type and (optionally) by release tag.

## When to use

- Before cutting a release, to draft the next `CHANGELOG.md` entry.
- To backfill a changelog for a repo that never had one.
- In CI, to keep a "Unreleased" section current.

## Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `--from` | last tag | Start ref (exclusive). |
| `--to` | `HEAD` | End ref (inclusive). |
| `--version` | `Unreleased` | Version heading for the generated section. |
| `--date` | today (ISO) | Release date. |
| `--out` | `CHANGELOG.md` | Output file. Prepends to existing file. |
| `--stdout` | off | Print instead of writing. |

## Procedure

1. **Enumerate commits** in the range, newest-last:
   ```bash
   git log --no-merges --pretty=format:'%H%x1f%s%x1f%b%x1e' "$FROM..$TO"
   ```
   Use `%x1f` (unit separator) between fields and `%x1e` (record separator)
   between commits so commit bodies containing newlines never break parsing.

2. **Classify** each commit by [Conventional Commits](https://www.conventionalcommits.org/)
   type parsed from the subject (`feat`, `fix`, `docs`, `perf`, `refactor`,
   `test`, `build`, `ci`, `chore`, `revert`). Non-conforming subjects → `Other`.

3. **Map types to Keep a Changelog sections**:

   | Conventional type | CHANGELOG section |
   |-------------------|-------------------|
   | `feat` | Added |
   | `fix` | Fixed |
   | `perf` | Changed |
   | `refactor`, `build`, `ci`, `chore` | Changed |
   | `docs` | Documentation |
   | `revert` | Removed |
   | everything else | Other |

4. **Detect breaking changes**: a `!` after the type (`feat!:`) or a
   `BREAKING CHANGE:` footer. Collect these into a top-level **Breaking**
   section that appears *before* the others.

5. **Render** the section:
   ```markdown
   ## [1.4.0] - 2026-10-13

   ### Breaking
   - **api:** drop `v1` endpoints (#123)

   ### Added
   - add CSV export (#120)

   ### Fixed
   - correct timezone drift in scheduler (#121)
   ```
   Each bullet: `- <scope>: <subject> (#PR)` — scope and PR number are extracted
   from the commit subject/footer when present.

6. **Prepend** (never overwrite) to `CHANGELOG.md`, preserving the Keep a
   Changelog header if the file already exists. If it does not exist, emit the
   standard header first.

## Rules

- **Deterministic**: same range → same output. Sort within each section by
  commit order (oldest first), not alphabetically.
- **No network**: works fully offline from local git history.
- **Idempotent**: re-running for the same `--version` replaces that version's
  section rather than duplicating it.
- **Never lose data**: always prepend; never truncate prior entries.

## Reference implementation

See [`scripts/changelog.py`](./scripts/changelog.py) — a dependency-free
Python 3 script that implements the procedure above. Run:

```bash
python3 scripts/changelog.py --from v1.3.0 --to HEAD --version 1.4.0
```

## Example

```bash
# Draft the Unreleased section from the last tag to HEAD
python3 scripts/changelog.py --stdout

# Cut a release entry
python3 scripts/changelog.py --from v1.3.0 --version 1.4.0 --date 2026-10-13
```
