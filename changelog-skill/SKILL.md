---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a project's git history, auto-categorizing commits into Added / Fixed / Changed / Removed since the last tag.
---

# Generate Changelog

Turn a repo's git history into a clean, categorized `CHANGELOG.md`.

## When to use
- The user asks for a changelog, release notes, or "what changed since the last release".
- Before cutting a release/tag.

## How to run
Run the bundled script from the repository root:

```bash
bash changelog.sh            # writes CHANGELOG.md (commits since last tag)
bash changelog.sh --all      # full history, ignoring tags
bash changelog.sh -o out.md  # custom output path
```

## Categorization rules
- `feat:` / `add` → **Added**
- `fix:` → **Fixed**
- `refactor:` `perf:` `style:` `docs:` `test:` `chore:` `build:` `ci:` → **Changed**
- subject contains *remove*/*delete* → **Removed**
- anything else → **Changed**

## Output
A `CHANGELOG.md` with a dated `## <version>` heading and the four sections.
