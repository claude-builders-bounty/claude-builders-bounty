---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commit history since the latest tag. Use this when a user asks for /generate-changelog, release notes, or a changelog generated from git history.
---

# Generate Changelog

Use the bundled `scripts/changelog.sh` script from the target repository root:

```bash
bash scripts/changelog.sh
```

If the script is kept in this skill folder, either copy it to the target repository's `scripts/` directory or run it by absolute path from the repository root.

## Workflow

1. Confirm the current directory is a git repository.
2. Run the script to collect commits since the latest reachable tag. If no tags exist, it uses the full repository history.
3. Review `CHANGELOG.md` and adjust wording only if project-specific context is needed.

## Categorization

The script classifies commit subjects into:

- `Added`: feature, add, create, implement, introduce.
- `Fixed`: fix, bug, patch, repair, resolve.
- `Changed`: change, update, refactor, chore, docs, test, perf, style, ci, build.
- `Removed`: remove, delete, drop, deprecate.

Each changelog bullet includes the original commit subject and short hash for traceability.
