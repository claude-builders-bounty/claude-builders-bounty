# Generate Changelog

Use this skill when a user asks for `/generate-changelog` or wants a structured `CHANGELOG.md` generated from Git history.

## Workflow

1. Confirm the current directory is the target Git repository.
2. Run:

   ```bash
   bash changelog.sh
   ```

3. Open `CHANGELOG.md`, check that the categories match the commit history, and adjust wording only if the user asks for editorial cleanup.

## Behavior

- Reads commits since the latest Git tag.
- Falls back to all reachable commits when the repository has no tags.
- Groups entries into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Markdown changelog suitable for review before release.
