# Generate CHANGELOG Skill

This Claude Code skill provides a simple command to generate a structured `CHANGELOG.md` from the git history of the current repository.

## Command

```
/generate-changelog
```

When invoked, the skill runs the `generate-changelog.sh` script located at the repository root. The script:

1. Detects the most recent git tag (or uses the full history if no tag exists).
2. Retrieves commits since that tag.
3. Classifies commits into **Added**, **Fixed**, **Changed**, and **Removed** based on conventional commit prefixes.
4. Produces a `CHANGELOG.md` following the *Keep a Changelog* format.

## Usage Steps (3 steps)

1. Ensure the repository is a git repository and has at least one commit.
2. Run the skill via the `/generate-changelog` command or execute the script directly:
   ```bash
   chmod +x generate-changelog.sh
   ./generate-changelog.sh
   ```
3. The `CHANGELOG.md` file will be created/updated at the repository root.

## Sample Output

```markdown
# Changelog

## [Unreleased]

### Added
- feat: initial feature ([`a1b2c3d`](https://github.com/user/repo/commit/a1b2c3d))

### Fixed
- fix: resolve login bug ([`d4e5f6g`](https://github.com/user/repo/commit/d4e5f6g))
```

The skill works out‑of‑the‑box with no external dependencies.
