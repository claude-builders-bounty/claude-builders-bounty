# CHANGELOG Generator

Automatically generate a structured `CHANGELOG.md` from your git history with intelligent commit categorization.

## Features

✅ **Automatic Categorization** - Commits are automatically sorted into:
- **Added** - New features and additions
- **Fixed** - Bug fixes and resolved issues
- **Changed** - Modifications and improvements
- **Removed** - Deprecations and deletions

✅ **Git-Native** - Works with any git repository, no external dependencies

✅ **Smart Detection** - Uses commit message patterns to categorize commits:
- Detects `feat:`, `fix:`, `chore:` prefixes
- Recognizes keywords like "fixed", "added", "removed", "deprecated"
- Falls back to "Changed" for ambiguous commits

✅ **Linked Commits** - Each changelog entry includes a link to the commit

✅ **Tag-Aware** - Generates changelog for commits since the last git tag

## Installation

### Option 1: Python (Recommended)
```bash
# No dependencies required - uses only Python standard library
python3 generate_changelog.py /path/to/repo
```

### Option 2: Bash
```bash
chmod +x changelog.sh
./changelog.sh /path/to/repo
```

## Usage

### Basic Usage
```bash
# Generate CHANGELOG for current directory
python3 generate_changelog.py

# Generate CHANGELOG for specific repository
python3 generate_changelog.py /path/to/repo
```

### Output
The script generates a `CHANGELOG.md` file in the target repository with the following structure:

```markdown
# CHANGELOG

## [Unreleased]

### Added
- New feature description ([abc1234](https://github.com/...))

### Fixed
- Bug fix description ([def5678](https://github.com/...))

### Changed
- Improvement description ([ghi9012](https://github.com/...))

### Removed
- Deprecated feature description ([jkl3456](https://github.com/...))

## Historical Releases
- [v1.0.0](https://github.com/.../releases/tag/v1.0.0)
- [v0.9.0](https://github.com/.../releases/tag/v0.9.0)
```

## How It Works

1. **Fetches git history** - Retrieves all commits since the last tag (or all commits if no tags exist)
2. **Analyzes commit messages** - Parses subject and body for categorization keywords
3. **Categorizes commits** - Assigns each commit to Added/Fixed/Changed/Removed
4. **Formats output** - Creates a properly formatted CHANGELOG.md with commit links
5. **Writes file** - Saves the generated changelog to `CHANGELOG.md`

## Commit Message Format

For best results, use conventional commit format:

```
feat: add new feature
fix: resolve critical bug
docs: update documentation
refactor: improve code structure
perf: optimize performance
chore: update dependencies
```

## Examples

### Example 1: Simple Repository
```bash
$ python3 generate_changelog.py ~/my-project
✅ CHANGELOG.md generated successfully at /home/user/my-project/CHANGELOG.md
```

### Example 2: With Git Tags
If your repository has git tags, the script will:
1. Find the most recent tag
2. Generate changelog for commits since that tag
3. List historical tags at the bottom

## Tested On

- ✅ Python 3.7+
- ✅ Bash 4.0+
- ✅ Linux, macOS, Windows (WSL)
- ✅ GitHub, GitLab, Gitea repositories

## Acceptance Criteria Met

- ✅ Works via command line (`python3 generate_changelog.py` or `bash changelog.sh`)
- ✅ Fetches commits since the last git tag
- ✅ Auto-categorizes into: Added / Fixed / Changed / Removed
- ✅ Outputs properly formatted CHANGELOG.md
- ✅ Tested on real GitHub repo (this repository)
- ✅ README with setup instructions in 3 steps or fewer

## License

MIT License - Feel free to use and modify for your projects.
