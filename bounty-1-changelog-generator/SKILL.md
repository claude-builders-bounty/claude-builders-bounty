# generate-changelog

Generate a structured CHANGELOG.md from git history, auto-categorized into Added/Fixed/Changed/Removed.

## Usage

Run `bash changelog.sh` in any git repository, or use the `/generate-changelog` command in Claude Code.

## Instructions

When the user runs `/generate-changelog`:

1. Detect the last git tag: `git describe --tags --abbrev=0`
2. If no tag exists, use full history
3. Fetch all commits since that tag: `git log <tag>..HEAD --pretty=format:"%s" --no-merges`
4. Categorize each commit:
   - **Added**: commits starting with `feat`, `add`, `new`, `create`, `implement`
   - **Fixed**: commits starting with `fix`, `bug`, `patch`, `resolve`
   - **Changed**: commits starting with `refactor`, `change`, `update`, `improve`, `chore`, `docs`, `style`, `build`, `ci`, `test`, `perf`
   - **Removed**: commits containing `remove`, `delete`, `drop`, `deprecat`
5. Generate `CHANGELOG.md` in Keep a Changelog format
6. Report the number of commits categorized

Alternatively, run the provided bash script:
```bash
bash changelog.sh              # Since last tag
bash changelog.sh v1.0.0       # Since specific tag
bash changelog.sh --all        # Full history
```
