# Generate Changelog

Use this skill when the user asks to generate or refresh a `CHANGELOG.md` from
git history.

## Workflow

1. Confirm the current directory is the target git repository.
2. Run:

   ```bash
   bash skills/generate-changelog/changelog.sh
   ```

3. Inspect the generated `CHANGELOG.md` for obvious categorization mistakes.
4. Report the latest tag used, number of commits grouped, and output path.

## Behavior

The script:

- Finds the latest git tag with `git describe --tags --abbrev=0`.
- Reads commits since that tag, or all commits when no tag exists.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Keep-a-Changelog-style Markdown file.

Do not invent release notes that are not backed by git commits.
