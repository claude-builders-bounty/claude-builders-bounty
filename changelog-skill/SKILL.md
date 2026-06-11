# Generate Changelog

Generate a structured `CHANGELOG.md` from git history, auto-categorized by change type.

## Usage

### Bash (recommended)
```bash
./changelog.sh
```

### Claude Code
```
/generate-changelog
```

## What It Does

1. Fetches all commits since the last git tag (or all commits if no tags exist)
2. Parses conventional commit messages (`feat:`, `fix:`, `refactor:`, etc.)
3. Auto-categorizes into: **Added** / **Fixed** / **Changed** / **Removed**
4. Detects breaking changes (`!` suffix or `BREAKING CHANGE:`)
5. Outputs a properly formatted `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) format

## Setup (3 steps)

1. Copy `changelog.sh` to your project root
2. Make it executable: `chmod +x changelog.sh`
3. Run it: `./changelog.sh`

## How It Works

### Commit Parsing

The script parses commit messages using [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>
```

**Supported types:**
| Type | Changelog Section |
|------|-------------------|
| `feat` | Added |
| `fix` | Fixed |
| `refactor` | Changed |
| `perf` | Changed |
| `docs` | Changed |
| `chore` | Changed |
| `build` | Changed |
| `ci` | Changed |
| `revert` | Removed |

**Breaking changes:**
- `feat!:` → Added **and** ⚠️ Breaking Changes
- `fix!:` → Fixed **and** ⚠️ Breaking Changes
- `BREAKING CHANGE:` in message → ⚠️ Breaking Changes

### Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### ⚠️ Breaking Changes

- change API response format (#456)

### Added

- **auth**: add OAuth2 login flow (#123)
- implement dark mode toggle (#789)

### Fixed

- **payments**: fix race condition in payment processing (#456)

### Changed

- upgrade dependencies to latest versions (#012)

### Removed

- deprecated legacy API endpoints (#345)
```

## Edge Cases

- **Non-conventional commits**: Categorized as "Changed" with original message
- **Merge commits**: Skipped by default (`--no-merges`)
- **Multiple tags**: Uses the most recent tag
- **Empty history**: Outputs "No changes found" message
- **Breaking changes**: Detected from `!` suffix or `BREAKING CHANGE:` in message
- **Commits with PR numbers**: Automatically extracted from `(#NNN)` pattern

## Customization

Edit `changelog.sh` to:
- Add custom commit type mappings
- Change section ordering
- Include/exclude specific authors
- Filter by date range
- Add custom headers/footers

## Example Output

See [SAMPLE_CHANGELOG.md](./SAMPLE_CHANGELOG.md) for a real-world example generated from a project with 50+ commits.

## Dependencies

- `git` (any version)
- `bash` 4.0+
- No external tools required (pure bash + git)

## Testing

Tested on:
- macOS (bash 5.x)
- Linux (bash 4.x, 5.x)
- WSL2 (bash 5.x)
- Git 2.x

## License

MIT
