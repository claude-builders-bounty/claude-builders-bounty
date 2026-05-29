# Generate Changelog

Use this skill when the user asks to generate, refresh, or bootstrap a `CHANGELOG.md` from a git repository's commit history.

## Workflow

1. From the repository root, run:

   ```bash
   bash changelog.sh
   ```

2. Review the generated `CHANGELOG.md` sections:

   - `Added`
   - `Fixed`
   - `Changed`
   - `Removed`
   - `Uncategorized` when a commit cannot be classified safely

3. Commit the generated changelog after checking that the categories match the project conventions.

## Behavior

- Uses commits since the most recent git tag.
- If no tag exists, uses the full project history.
- Ignores merge commits.
- Categorizes conventional commit prefixes such as `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`, `remove`, and related plain-English prefixes.
- Writes a standard Markdown `CHANGELOG.md`.

## Safety

The script only reads git history and writes the changelog output file. It does not push, tag, delete files, or contact external services.
