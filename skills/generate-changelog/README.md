# generate-changelog — categorized CHANGELOG.md from git history

Turns your commit history into a Keep-a-Changelog file, sorted into
**Added / Fixed / Changed / Removed**.

Uses Conventional Commit prefixes when they're there and falls back to keyword matching when
they aren't, so it works on a repo that never adopted the convention.

## Install (3 steps)

1. Copy this folder to `~/.claude/skills/generate-changelog/`.
2. Copy `commands/generate-changelog.md` to `~/.claude/commands/generate-changelog.md`.
3. In any git repo, run `/generate-changelog 1.4.0`.

## Usage

```bash
python changelog.py                              # since last tag -> ./CHANGELOG.md
python changelog.py --dry-run                    # print, don't write
python changelog.py --version 1.4.0              # heading instead of "Unreleased"
python changelog.py --from v1.2.0 --to v1.3.0    # explicit range
bash changelog.sh --dry-run                      # same, via the wrapper
```

Run it from the repo root. Range defaults to `<last-tag>..HEAD`; with no tags it walks all
history. The baseline tag itself is excluded.

## How commits are categorized

| Category | Sources |
|---|---|
| Added | `feat`, `feature`, `add`, `new`; keywords add/implement/introduce/support/new |
| Fixed | `fix`, `bugfix`, `hotfix`, `patch`; keywords fix/repair/correct/resolve/patch |
| Removed | `remove`, `revert`, `deprecate`, `drop`, `delete`; keywords remove/revert/deprecate/drop/delete |
| Changed | `refactor`, `perf`, `chore`, `docs`, `ci`, `test`, `build`, `style`; keywords update/change/refactor/improve/tweak/bump/rename/move |

Merge commits are skipped. Anything unmatched lands in `Changed` rather than being dropped.
A conventional prefix is stripped and any scope is preserved: `feat(auth): add OAuth` becomes
`- **auth:** add OAuth (cace3e0)`.

## Output

```markdown
# Changelog

All notable changes to this project.

## [1.1.0] - 2026-10-17

### Added
- **auth:** add OAuth login (cace3e0)
- new dark mode toggle (3e21b19)

### Fixed
- **api:** resolve null deref on 404 (7137f73)
```

Re-running prepends the newest section above the previous one, so the file stays
newest-first. Existing file content above the first `##` heading is preserved.

## Tests

```
python test_changelog.py
```

Builds a real throwaway git repo with a tagged baseline and 12 commits, then asserts
categorization, prefix stripping, sha attachment, baseline exclusion, the write path,
newest-first insertion, explicit ranges, and the non-repo error path.
