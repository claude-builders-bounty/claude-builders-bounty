# Changelog Generator Skill

Generates a structured CHANGELOG.md from git commit history.

## Command

```
/generate-changelog
```

## How It Works

1. Gets the last git tag via `git describe --tags --abbrev=0`
2. Fetches all commits since that tag (or all commits if no tag exists)
3. Auto-categorizes commits by prefix:
   - `feat:`, `add:` → **Added**
   - `fix:`, `bugfix:` → **Fixed**
   - `chore:`, `refactor:`, `update:` → **Changed**
   - `remove:`, `delete:` → **Removed**
   - `docs:` → **Documentation**
   - `perf:`, `optimize:` → **Performance**
   - `test:` → **Testing**
4. Outputs `CHANGELOG.md` in Keep a Changelog format

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--repo <path>` | Path to git repository | Current directory |
| `--output <file>` | Output file path | `./CHANGELOG.md` |
| `--from-tag <tag>` | Start from specific tag | Last tag |
| `--all` | Include all commits (ignore tags) | false |

## Example Output

```markdown
# Changelog

## [Unreleased]

### Added
- New feature implementation
- User authentication module

### Fixed
- Resolved login timeout issue
- Fixed memory leak in data processor
```

## Requirements

- Git repository
- Standard Unix tools (bash, grep, sed)
