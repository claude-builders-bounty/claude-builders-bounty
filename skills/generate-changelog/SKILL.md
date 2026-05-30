---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history for a repository. Use when the user asks for a changelog, release notes, or grouped commit summary from git commits, especially when changes should be categorized into Added, Fixed, Changed, and Removed sections with links back to commits since the latest git tag.
---

# Generate Changelog

Use this skill to create or update `CHANGELOG.md` from the current repository's git history.

## Workflow

1. Inspect existing release files:
   - `CHANGELOG.md`
   - `RELEASE.md`
   - GitHub releases or version tags if available.
2. Choose the commit range:
   - If the user gives a range, use it exactly.
   - If tags exist and no range is given, use the latest tag through `HEAD`.
   - If no tags exist, use all available commits.
3. Run the helper:

```bash
bash changelog.sh
```

4. Review the generated groups and edit any entries that need clearer wording.
5. Preserve existing hand-written changelog content unless the user asks to regenerate the file.

## Categories

Map commits to these sections:

- `Fixed`: bug fixes and regressions.
- `Added`: new features, new commands, new files, support for new platforms.
- `Changed`: behavior changes, refactors, chores, dependency updates, docs, CI, or uncategorized work.
- `Removed`: deleted features, APIs, or files.

Use `Changed` when a commit does not clearly fit another category.

## Output Rules

- Use Keep a Changelog-style Markdown.
- Include an `Unreleased` section unless the user provides a release version.
- Link each entry to the short commit hash when the remote URL can be detected.
- Keep entries concise and readable. Rewrite raw commit subjects only when the meaning stays the same.
- Do not invent issues, PR numbers, versions, or dates.
- If merge commits are noisy, omit them unless they are the only useful history.

## Verification

After generation, confirm:

- `CHANGELOG.md` exists.
- The selected commit range is stated in the file.
- Each included commit appears once.
- Categories are present only when they have entries.
