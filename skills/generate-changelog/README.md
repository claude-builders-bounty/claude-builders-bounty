# Generate Changelog

A Python script that generates a structured `CHANGELOG.md` from git history. Zero external dependencies.

## Setup (3 Steps)

1. **Copy the `skills/generate-changelog/` folder** into your project
2. **Make the script executable**: `chmod +x skills/generate-changelog/changelog.py`
3. **Run it**: `python3 skills/generate-changelog/changelog.py`

That's it. The script auto-detects your last git tag and categorizes commits.

## Usage

### Python (recommended)

```bash
# Default: writes CHANGELOG.md to current directory
python3 skills/generate-changelog/changelog.py

# Preview without writing
python3 skills/generate-changelog/changelog.py --dry-run

# Since a specific tag
python3 skills/generate-changelog/changelog.py --since v1.0.0

# Custom output file
python3 skills/generate-changelog/changelog.py --output docs/CHANGELOG.md

# Override version header
python3 skills/generate-changelog/changelog.py --version 2.1.0
```

### Claude Code

Place `SKILL.md` in your `.claude/skills/` directory, then invoke `/generate-changelog` in Claude Code.

## How It Works

- Finds the latest git tag (or uses all commits if no tags exist)
- Scans commits with `git log --no-merges`
- Categorizes by conventional commit prefix + natural language keywords:
  - `feat:`, `add:`, `new:` → **Added**
  - `fix:`, `bug:`, `patch:` → **Fixed**
  - `refactor:`, `perf:`, `chore:`, `docs:` → **Changed**
  - `remove:`, `delete:`, `drop:` → **Removed**
  - `security:`, `vuln:`, `cve:` → **Security**
  - No recognized prefix → **Changed** (default)
- Outputs a Keep-a-Changelog formatted `CHANGELOG.md`

## Supported Commit Prefixes

| Prefix | Category |
|--------|----------|
| `feat:`, `add:`, `new:`, `implement:` | Added |
| `fix:`, `bug:`, `patch:`, `hotfix:` | Fixed |
| `refactor:`, `perf:`, `chore:`, `docs:`, `ci:` | Changed |
| `remove:`, `delete:`, `drop:`, `deprecate:` | Removed |
| `security:`, `vuln:`, `cve:`, `xss:` | Security |
| _(none)_ | Changed (default) |

## Requirements

- Python 3.7+
- Git repository with commit history

## Sample Output

See `SAMPLE_OUTPUT.md` for a real example generated from [cli/cli](https://github.com/cli/cli).
