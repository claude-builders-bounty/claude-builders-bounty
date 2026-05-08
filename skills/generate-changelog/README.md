# Generate Structured CHANGELOG from Git History

A Claude Code skill + standalone bash script that automatically generates a `CHANGELOG.md` from your project's git history.

## Quick Start (3 steps)

1. **Copy** this `generate-changelog/` folder into your project's `skills/` directory
2. **Run** `bash skills/generate-changelog/changelog.sh` to generate your changelog
3. **Commit** the generated `CHANGELOG.md` to your repository

## Usage

### As a Claude Code Skill

```
/generate-changelog
```

### As a Standalone Script

```bash
# Generate changelog from last tag to HEAD
bash changelog.sh

# Specify a starting tag
bash changelog.sh --since-tag v1.0.0

# Dry run (print to stdout)
bash changelog.sh --dry-run

# Custom output file
bash changelog.sh --output docs/CHANGES.md

# Different repo path
bash changelog.sh --repo /path/to/repo
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--since-tag <tag>` | Start from this tag | Last git tag |
| `--output <file>` | Output file path | `CHANGELOG.md` |
| `--repo <path>` | Path to git repository | `.` |
| `--dry-run` | Print to stdout instead of file | off |
| `-h, --help` | Show help message | — |

## How It Works

1. Finds the most recent git tag (or uses `--since-tag`)
2. Collects all commits between that tag and `HEAD`
3. Categorizes each commit by [Conventional Commits](https://www.conventionalcommits.org/) prefix or keyword detection
4. Outputs a properly formatted `CHANGELOG.md` in [Keep a Changelog](https://keepachangelog.com/) format

### Categorization Rules

| Category | Conventional Prefixes | Keywords |
|----------|----------------------|----------|
| **Added** | `feat:` | add, new, create, introduce, implement, support |
| **Fixed** | `fix:`, `bugfix:`, `hotfix:` | fix, resolve, repair, patch, correct, handle |
| **Changed** | `refactor:`, `update:`, `change:`, `improve:` | update, change, modify, improve, adjust, refactor, migrate, upgrade |
| **Removed** | `remove:`, `delete:`, `drop:`, `deprecate:` | remove, delete, drop, deprecate, eliminate, strip |
| **Other** | — | Anything not matching the above |

## Sample Output

See [SAMPLE_OUTPUT.md](./SAMPLE_OUTPUT.md) for a real example generated from the [jq](https://github.com/jqlang/jq) repository.

## Requirements

- Git 2.0+
- Bash 3.2+

No additional dependencies.
