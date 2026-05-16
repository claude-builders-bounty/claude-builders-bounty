# generate-changelog

Generate a structured `CHANGELOG.md` from git history. Auto-categorizes commits into **Added** / **Fixed** / **Changed** / **Removed** using [Conventional Commits](https://www.conventionalcommits.org/) parsing. Zero dependencies — stdlib only.

## Quick Start

```bash
# 1. Copy the script to your project
cp changelog.sh generate_changelog.py /your/project/

# 2. Make executable (Linux/macOS)
chmod +x changelog.sh

# 3. Run it
bash changelog.sh
```

Outputs `CHANGELOG.md` in the current directory.

## How It Works

1. Finds the latest git tag
2. Collects all commits since that tag
3. Parses Conventional Commit prefixes (`feat:`, `fix:`, `refactor:`, etc.)
4. Auto-categorizes into sections
5. Writes formatted `CHANGELOG.md`

### Category Mapping

| Commit prefix | Section |
|--------------|---------|
| `feat:`, `feature:` | Added |
| `fix:`, `bugfix:`, `hotfix:` | Fixed |
| `refactor:`, `style:`, `perf:` | Changed |
| `revert:`, `remove:`, `deprecate:` | Removed |
| `docs:` | Documentation |
| `test:` | Testing |
| `ci:` | CI/CD |
| `build:` | Build |
| `chore:` | Maintenance |

Non-conventional commits are categorized by keyword analysis.

## Options

```bash
python generate_changelog.py --repo /path/to/repo --output docs/CHANGELOG.md --since v1.0.0
```

| Flag | Default | Description |
|------|---------|-------------|
| `--repo` | `.` | Path to git repository |
| `--output` / `-o` | `CHANGELOG.md` | Output file path |
| `--since` | latest tag | Start from a specific git ref |

## Claude Code Integration

Copy `SKILL.md` into your Claude Code skills directory. Then use `/generate-changelog` to generate changelogs from within Claude Code.

## Sample Output

See [sample-CHANGELOG.md](sample-CHANGELOG.md) — generated from a real repository (Hermes Agent, 10 commits across 5 categories).
