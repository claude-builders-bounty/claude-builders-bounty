# Generate Changelog

Generate a structured CHANGELOG.md from the project's git history.

## Usage

When invoked via `/generate-changelog`, this skill analyzes git commits since the last tag and produces a properly formatted changelog.

## Instructions

1. Get the last git tag:
   ```bash
   LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
   ```

2. Fetch commits since that tag (or all commits if no tags):
   ```bash
   if [ -n "$LAST_TAG" ]; then
     git log "$LAST_TAG..HEAD" --pretty=format:"%s"
   else
     git log --pretty=format:"%s"
   fi
   ```

3. Categorize each commit by analyzing its message:
   - **Added**: Commits starting with `feat`, `add`, `new`, `create`, `implement`, `introduce`
   - **Fixed**: Commits starting with `fix`, `bug`, `patch`, `resolve`, `close`, `correct`
   - **Removed**: Commits starting with `remove`, `delete`, `drop`, `deprecate`
   - **Changed**: All other commits

4. Generate CHANGELOG.md with this structure:
   ```markdown
   # Changelog

   All notable changes to this project will be documented in this file.

   ## [VERSION] - YYYY-MM-DD

   ### Added
   - Commit message 1
   - Commit message 2

   ### Fixed
   - Fix commit 1

   ### Changed
   - Change commit 1

   ### Removed
   - Removed item 1
   ```

5. Write the output to `CHANGELOG.md` in the project root.

## Alternative: Bash Script

Run the included bash script directly:

```bash
bash changelog.sh
```

Options:
- `--since TAG`: Generate changelog since a specific tag
- `--output FILE`: Specify output file (default: CHANGELOG.md)

## Output Format

The generated changelog follows [Keep a Changelog](https://keepachangelog.com/) format with automatic categorization based on conventional commit prefixes.
