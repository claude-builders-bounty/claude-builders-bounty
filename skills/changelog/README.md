# Changelog Generator

Automatically generates a structured `CHANGELOG.md` from git commit history.

## Quick Setup (3 Steps)

### 1. Copy the script
```bash
cp scripts/generate-changelog.sh ~/your-project/scripts/
```

### 2. Make it executable
```bash
chmod +x ~/your-project/scripts/generate-changelog.sh
```

### 3. Run it
```bash
cd ~/your-project
./scripts/generate-changelog.sh
```

## Usage

```bash
# Basic usage (from last tag)
./scripts/generate-changelog.sh

# Specify repository path
./scripts/generate-changelog.sh --repo /path/to/repo

# Output to custom location
./scripts/generate-changelog.sh --output /path/to/CHANGELOG.md

# Include all commits (ignore tags)
./scripts/generate-changelog.sh --all

# Start from specific tag
./scripts/generate-changelog.sh --from-tag v1.0.0
```

## Auto-categorization

Commits are automatically sorted into categories based on conventional commit prefixes:

| Prefix | Category |
|--------|----------|
| `feat:`, `add:` | **Added** |
| `fix:`, `bugfix:` | **Fixed** |
| `chore:`, `refactor:`, `update:` | **Changed** |
| `remove:`, `delete:` | **Removed** |
| `docs:` | **Documentation** |
| `perf:`, `optimize:` | **Performance** |
| `test:` | **Testing** |
| Other | **Other** |

## Example Output

```markdown
# Changelog

## [v1.2.0]

### Added
- User authentication module
- New API endpoints

### Fixed
- Resolved login timeout issue
```

## Demo

This skill was tested on this repository. Run:

```bash
cd /Users/biuom-mini/.hermes/hermes-agent/claude-builders-bounty
./scripts/generate-changelog.sh --repo .
```

Output saved to `CHANGELOG.md`.
