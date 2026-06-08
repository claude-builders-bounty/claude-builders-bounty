---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the latest tag.
---

# Generate Changelog

Use this skill when the user asks for `/generate-changelog`, a release summary,
or a `CHANGELOG.md` generated from the current git history.

## Workflow

1. Confirm the current directory is the target git repository.
2. Run the bundled script:

   ```bash
   bash scripts/changelog.sh
   ```

3. Review the generated `CHANGELOG.md` and adjust wording only when a commit
   subject is ambiguous.

## Behavior

- Reads commits since the latest git tag, or the full history when no tag exists.
- Groups commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.
- Supports Conventional Commit prefixes such as `feat:`, `fix:`, `docs:`,
  `refactor:`, and `chore:`.
- Includes commit links when the repository has a GitHub `origin` remote.
- Skips merge commits to keep the changelog focused on shipped changes.

## Options

```bash
bash scripts/changelog.sh --output RELEASE_NOTES.md
bash scripts/changelog.sh --repo-url https://github.com/org/repo
```

Environment variables are also supported:

```bash
CHANGELOG_OUTPUT=RELEASE_NOTES.md bash scripts/changelog.sh
CHANGELOG_REPO_URL=https://github.com/org/repo bash scripts/changelog.sh
```
