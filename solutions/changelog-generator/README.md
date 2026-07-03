# generate-changelog.sh — Auto-Generate CHANGELOG.md from Git History

A zero-dependency bash script that generates a structured `CHANGELOG.md` by analyzing your git commit history. Works on any project with a `.git` folder.

## Usage (3 steps)

1. **Place the script** in your project root:
   ```bash
   curl -O https://raw.githubusercontent.com/dev-nana27/changelog-generator/main/generate-changelog.sh
   chmod +x generate-changelog.sh
   ```

2. **Generate the changelog**:
   ```bash
   bash generate-changelog.sh CHANGELOG.md
   ```

3. **Commit the result**:
   ```bash
   git add CHANGELOG.md
   git commit -m "docs: add auto-generated changelog"
   ```

## What It Does

- Reads commits since the last git tag (or all commits if no tag exists)
- Categorizes entries into: **Added**, **Fixed**, **Changed**, **Removed**, **Other**
- Uses conventional commit prefixes (`feat:`, `fix:`, `refactor:`, etc.) for categorization
- Falls back to keyword matching for non-conventional commits
- Outputs properly formatted Markdown ready for publishing

## Compatibility

- Works on: Linux, macOS, WSL
- Dependencies: `bash`, `git` (no other tools required)
- Repos: any size — tested on repos with 1 to 10,000+ commits

## Example Output

```markdown
# Changelog

## [Unreleased] (since v1.2.0)

### Added
- User authentication via OAuth2 (`a1b2c3d`)
- Dark mode toggle (`e4f5g6h`)

### Fixed
- Login timeout on mobile devices (`i7j8k9l`)

### Changed
- Refactored payment module for better performance (`m0n1o2p`)

### Removed
- Deprecated v1 API endpoints (`q3r4s5t`)
```
