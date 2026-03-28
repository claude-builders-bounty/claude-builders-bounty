# Git Changelog Generator

A Claude Code skill that automatically generates a structured `CHANGELOG.md` from a project's git history.

## Features

- ✅ Auto-categorizes commits into `Added` / `Fixed` / `Changed` / `Removed`
- ✅ Supports [Conventional Commits](https://www.conventionalcommits.org/) format
- ✅ Generates links to commits (GitHub/GitLab compatible)
- ✅ Fetches commits since the last git tag
- ✅ Follows [Keep a Changelog](https://keepachangelog.com/) format

## Setup (3 Steps)

### 1. Install the Skill

Place the `git-changelog` folder in your OpenClaw skills directory:

```bash
# Option A: Copy to workspace skills
cp -r git-changelog ~/.openclaw/workspace/skills/

# Option B: Install via ClawHub (if published)
clawhub install git-changelog
```

### 2. Verify Installation

The skill will automatically trigger when you mention "generate changelog" or use `/generate-changelog`.

### 3. Generate Your Changelog

```bash
# In any git repository:
python ~/.openclaw/workspace/skills/git-changelog/scripts/generate_changelog.py
```

That's it! Your `CHANGELOG.md` is now generated.

## Usage Examples

### Basic Usage

```bash
# Generate changelog since last tag
python generate_changelog.py

# Generate for a specific version
python generate_changelog.py --version 1.2.0

# Generate all commits (ignoring tags)
python generate_changelog.py --all
```

### Advanced Options

```bash
# Specify output file
python generate_changelog.py -o RELEASE_NOTES.md

# Generate from a specific tag
python generate_changelog.py --tag v1.0.0

# Specify repository path
python generate_changelog.py -r /path/to/repo

# Don't include commit links
python generate_changelog.py --no-links

# Prepend to existing CHANGELOG
python generate_changelog.py --prepend
```

### As a Claude Code Skill

Simply ask Claude:

```
Generate a changelog for this project
```

Or use the command:

```
/generate-changelog
```

## Commit Message Conventions

The script recognizes these conventional commit prefixes:

| Prefix | Category |
|--------|----------|
| `feat:`, `feature:`, `add:` | Added |
| `fix:`, `bugfix:`, `bug:` | Fixed |
| `update:`, `refactor:`, `improve:`, `change:` | Changed |
| `remove:`, `delete:`, `deprecate:` | Removed |

### Example Commits

```bash
feat: add user authentication        # → Added
fix: resolve login timeout issue     # → Fixed
refactor: improve database queries    # → Changed
remove: delete legacy API endpoints   # → Removed
```

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0]
### 2024-01-15

### Added
- User authentication system (a1b2c3d)
- Password reset functionality (e4f5g6h)
- Email validation on signup (i7j8k9l)

### Fixed
- Login redirect loop (m1n2o3p)
- Timezone issue in date picker (q4r5s6t)

### Changed
- Update dependencies to latest versions (u7v8w9x)
- Refactor database connection pooling (y1z2a3b)

### Removed
- Deprecated legacy API endpoints (c4d5e6f)
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Generate Changelog
  run: python scripts/generate_changelog.py --version ${{ github.event.inputs.version }}
```

### GitLab CI

```yaml
script:
  - python scripts/generate_changelog.py --version $CI_COMMIT_TAG
```

## Requirements

- Python 3.6+
- Git

## License

MIT License