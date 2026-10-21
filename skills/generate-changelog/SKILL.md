# Skill: generate-changelog

## Purpose
Build a structured `CHANGELOG.md` from git history: commits since the latest tag, grouped into Added / Fixed / Changed / Removed.

## Trigger
`/generate-changelog`

## When to use
- Release notes need a first draft from conventional (or keyword) commits
- Maintainers want a repeatable changelog without hand-sorting every commit

## Steps
1. Prefer `bash changelog.sh` at the repo root (script in this PR).
2. If the script is missing, run the equivalent: `git describe --tags --abbrev=0` for the last tag, then `git log <tag>..HEAD --pretty=format:'%h %s' --no-merges`.
3. Sort subjects:
   - **Added** — feat / add / new
   - **Fixed** — fix / bug / crash
   - **Changed** — refactor / chore / docs / perf / other
   - **Removed** — remove / delete / drop
4. Write `CHANGELOG.md` with those four sections. Do not edit application source for this task.

## Output shape
```markdown
# Changelog

Generated since vX.Y.Z.

## Added
- ...

## Fixed
- ...

## Changed
- ...

## Removed
- ...
```

## Notes
- No tags → use full history and label the range clearly.
- Keep merge commits out (`--no-merges`).
