# Changelog Generator

Automatically generate a structured `CHANGELOG.md` from your git history.

## Features

- ✅ Categorizes commits: Added, Fixed, Changed, Removed
- ✅ Auto-links to commits and authors
- ✅ Detects GitHub repos for automatic linking
- ✅ Preserves existing changelog content
- ✅ Follows Keep a Changelog format
- ✅ Zero dependencies (pure bash)

## Installation

```bash
# Download the script
curl -L -o generate-changelog https://raw.githubusercontent.com/plutuscontrol-ui/claude-builders-bounty/main/generate-changelog

# Make it executable
chmod +x generate-changelog

# Move to PATH (optional)
sudo mv generate-changelog /usr/local/bin/
```

Or use with npx:
```bash
npx generate-changelog
```

## Usage

```bash
# Generate CHANGELOG.md
generate-changelog

# Generate with custom filename
generate-changelog HISTORY.md

# In a CI/CD pipeline
generate-changelog && git add CHANGELOG.md && git commit -m "docs: Update changelog"
```

## How It Works

1. Fetches commits since the last git tag
2. Categorizes based on conventional commit patterns:
   - `feat:` or `add:` → **Added**
   - `fix:` or `bug:` → **Fixed**
   - `refactor:` or `update:` → **Changed**
   - `remove:` or `delete:` → **Removed**
   - Everything else → **Other**
3. Generates markdown with links to commits
4. Appends to existing changelog (if present)

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-03-28

### Added

- New user authentication system ([a1b2c3d](https://github.com/user/repo/commit/a1b2c3d) by Alice)
- Dark mode support ([b2c3d4e](https://github.com/user/repo/commit/b2c3d4e) by Bob)

### Fixed

- Login redirect loop ([c3d4e5f](https://github.com/user/repo/commit/c3d4e5f) by Carol)
```

## Testing

Tested on repositories:
- ✅ Linux/macOS
- ✅ GitHub repositories (auto-linking)
- ✅ GitLab repositories
- ✅ Bare git repos

## License

MIT
