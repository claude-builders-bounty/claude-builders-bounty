# CHANGELOG Generator

A standalone Python CLI tool that reads a git repository's history and generates a structured, well-formatted `CHANGELOG.md`. Fully supports the [Conventional Commits](https://www.conventionalcommits.org/) specification.

## Features

- 🏷️ **Tag-based versioning** — groups commits by semver tags (newest first), with an `Unreleased` section for HEAD commits
- 📝 **Conventional Commits** — recognises `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `perf:`, `test:`, `build:`, `ci:`, `revert:`, `security:`, `deprecate:`
- 💥 **Breaking change detection** — via `!` suffix (`feat!:`) or `BREAKING CHANGE:` in commit body
- 🔗 **Remote URL auto-detection** — links tag headers to GitHub/GitLab release pages
- 📄 **Multiple formats** — Markdown (default) or structured JSON
- 🎛️ **Flexible filtering** — `--since-tag` to scope the output
- ✅ **Zero external dependencies** — only the Python standard library

## Requirements

- Python 3.9+
- `git` available on `PATH`

## Installation

```bash
# No installation needed — just copy the script
curl -O https://raw.githubusercontent.com/.../changelog_generator.py
chmod +x changelog_generator.py
```

## Usage

```bash
# Generate CHANGELOG for the current directory (stdout)
python3 changelog_generator.py

# Specify a repo path
python3 changelog_generator.py --repo /path/to/repo

# Write to a file
python3 changelog_generator.py --output CHANGELOG.md

# Only show changes since a specific tag
python3 changelog_generator.py --since-tag v1.2.0

# Output as JSON
python3 changelog_generator.py --format json

# Strip emoji from output
python3 changelog_generator.py --no-emoji

# Provide a repo URL for tag links
python3 changelog_generator.py --repo-url https://github.com/org/repo
```

## CLI Options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--repo` | `-r` | `.` | Path to the git repository |
| `--since-tag` | `-s` | — | Only include this tag and newer |
| `--output` | `-o` | stdout | Output file path |
| `--format` | `-f` | `markdown` | Output format: `markdown` or `json` |
| `--no-emoji` | — | false | Strip emoji from Markdown output |
| `--repo-url` | — | auto | Remote URL for tag hyperlinks |

## Example Output

```markdown
# Changelog

> Generated automatically from git history.

## Unreleased — 2026-11-10

### 📚 Documentation

- add contribution guide ([`cea4219`])

### 🔧 Chores

- update CI pipeline ([`b7ee9ec`])

## v0.2.0 — 2026-11-09

### 💥 Breaking Changes

- **api:** redesign REST endpoints ([`6bdb8ba`])

### 🐛 Bug Fixes

- **auth:** resolve token expiry bug ([`7dd35e0`])

## v0.1.0 — 2026-11-01

### 🚀 Features

- initial commit ([`84b124b`])
```

## Running Tests

```bash
# Install pytest (only dependency — test runner only)
pip3 install pytest

# Run all 32 tests
python3 -m pytest tests/ -v
```

## Conventional Commits Reference

Supported commit types and their rendered section headings:

| Type | Section |
|------|---------|
| `feat` | 🚀 Features |
| `fix` | 🐛 Bug Fixes |
| `docs` | 📚 Documentation |
| `style` | 💅 Styles |
| `refactor` | ♻️ Refactoring |
| `perf` | ⚡ Performance |
| `test` | ✅ Tests |
| `build` | 🏗️ Build System |
| `ci` | 🤖 CI/CD |
| `chore` | 🔧 Chores |
| `revert` | ⏪ Reverts |
| `security` | 🔒 Security |
| `deprecate` | ⚠️ Deprecations |

Breaking changes (via `!` or `BREAKING CHANGE:` in body) always appear first under **💥 Breaking Changes**.

## License

MIT
