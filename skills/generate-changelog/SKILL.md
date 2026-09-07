---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag, auto-categorized into Added / Fixed / Changed / Removed.
---

# Generate changelog

## Trigger
User runs `/generate-changelog` or asks to generate/update `CHANGELOG.md` from commits.

## Steps
1. Confirm you are inside a git repository (`git rev-parse --show-toplevel`).
2. Run the bundled script from repo root:

```bash
bash changelog.sh
# or write to a custom path:
bash changelog.sh docs/CHANGELOG.md
```

3. Show the user the resulting `CHANGELOG.md` and a short summary of how many commits were classified into each section.

## Rules the script follows
- Range = commits since the newest git tag; if no tags exist, use all commits on `HEAD`.
- Skip merge commits.
- Categorize by conventional-commit prefixes and common verbs:
  - **Added** — `feat`, `feature`, `add`, introduce/create
  - **Fixed** — `fix`, `bugfix`, `hotfix`, `patch`
  - **Changed** — `chore`, `refactor`, `perf`, `style`, `docs`, `ci`, `build`, `update`, `change`, improve/bump
  - **Removed** — `remove`, `delete`, `drop`, `deprecate`
- Unmatched subjects fall into **Changed**.
- Output is Markdown with `Added` / `Fixed` / `Changed` / `Removed` sections.

## Do not
- Rewrite commit messages beyond listing them.
- Invent releases or version numbers.
- Force-push or modify git history.
