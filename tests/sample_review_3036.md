### Summary of Changes
This PR adds a zero-dependency Python script (`scripts/generate_changelog.py`) and a Bash wrapper (`changelog.sh`) to automatically generate a structured `CHANGELOG.md` file from the project's git history. The script groups commits by tags and automatically categorizes them into standard categories like `Added`, `Fixed`, `Changed`, and `Removed`.

### Identified Risks
- **Tag Date Parsing**: If a tag does not have a commit history date, it falls back to the current system date, which could lead to minor discrepancies if tags are backdated.
- **Commit Formatting**: Commits that do not follow conventional commit messages (e.g. "feat: ...", "fix: ...") default to the `Changed` category, which might clutter the section if the repository has unformatted messages.

### Improvement Suggestions
- **Custom Mapping**: Allow users to specify custom regex mappings for categories via an optional config file.
- **Output File Control**: Add a command line argument to output the changelog to standard output (stdout) or a custom file path, rather than overwriting `CHANGELOG.md` directly.

### Confidence Score
**High** - The script successfully categorizes commits, handles repositories with no tags gracefully, and includes 11 passing unit tests.
