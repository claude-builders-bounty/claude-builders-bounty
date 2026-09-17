---
name: generate-changelog
description: Use this when you need a structured CHANGELOG.md from git history since the last tag (Added / Fixed / Changed / Removed).
---

# Generate changelog

## Goal
Produce a Keep-a-Changelog-style `CHANGELOG.md` from commits since the latest git tag.

## Steps
1. Confirm you are in a git repo (`git rev-parse --show-toplevel`).
2. Run the companion script from the repo root:

```bash
bash path/to/changelog.sh
# or: bash path/to/changelog.sh CHANGELOG.md
```

3. Review the four sections: **Added**, **Fixed**, **Changed**, **Removed**.
4. Adjust any miscategorized lines, then commit the file if the user wants it saved.

## Slash-style trigger
When the user runs `/generate-changelog`, execute the script above and show a short summary of how many items landed in each section.

## Rules
- Prefer the last annotated/lightweight tag via `git describe --tags --abbrev=0`.
- If there is no tag, include all non-merge commits and note that in the header.
- Never invent commits; only use `git log` subjects.
- Do not force-push or rewrite history.
