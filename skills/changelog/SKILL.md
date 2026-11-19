---
name: generate-changelog
description: Audit the recent git history and write a structured CHANGELOG.md
---

Task:
1. Find the newest tag with `git describe --tags --abbrev=0`.
2. List commits since that tag with `git log <tag>..HEAD --no-merges --pretty=format:'%s'`.
3. Bucket subjects into Added / Fixed / Changed / Removed.
4. Write `CHANGELOG.md` at the repo root.

Example invocation:
```
/generate-changelog
```

Notes:
- Untagged repos: falls back to the full history.
- Added/new features → Added
- Fixes/patch/bugfix → Fixed
- Refactors/chores/docs/build → Changed
- Drop/retire/delete/remove → Removed
