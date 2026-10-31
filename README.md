# changelog-generator

A zero-dependency bash script that generates a structured `CHANGELOG.md` from your git history using conventional commit prefixes.

## Features

- **Tag-aware**: Automatically scopes changes to commits since the last git tag
- **Conventional commits**: Categorizes into `Added`, `Fixed`, `Changed`, `Removed`
- **Zero dependencies**: Pure bash + standard POSIX utilities
- **Graceful fallback**: Works on repos with no tags (uses full history)

## Setup (3 steps)

1. **Copy** `changelog.sh` into your project root:
   ```bash
   cp changelog.sh /path/to/your/project/
   ```

2. **Make executable**:
   ```bash
   chmod +x changelog.sh
   ```

3. **Run**:
   ```bash
   ./changelog.sh
   ```

That's it. Open `CHANGELOG.md` to see the result.

## Usage

```bash
# Generate CHANGELOG.md (default)
./changelog.sh

# Write to a custom file
./changelog.sh RELEASE_NOTES.md
```

## Commit prefix mapping

| Prefix                        | Category      |
| :---------------------------- | :------------ |
| `feat:`, `add:`, `new:`       | **Added**     |
| `fix:`, `bug:`, `patch:`      | **Fixed**     |
| `refactor:`, `perf:`, `chore:`, `style:`, `update:` | **Changed** |
| `remove:`, `delete:`, `revert:` | **Removed** |

Commits without a recognized prefix are filed under **Changed**.

## Sample output

```markdown
# Changelog

## [2026-10-31] — Changes since v1.2.0

### Added
- feat: add user avatar upload endpoint (`a1b2c3d`)
- feat(auth): support OAuth2 PKCE flow (`e4f5g6h`)

### Fixed
- fix: prevent null pointer on empty config (`i7j8k9l`)

### Changed
- refactor: extract database connection pool (`m0n1o2p`)
- chore: bump dependencies (`q3r4s5t`)
```

## Claude Code skill

This repo includes a `SKILL.md` that registers the `/generate-changelog` command. Drop both files into your project and the skill is available automatically.

## License

MIT
