# Claude Builders Bounty — CHANGELOG Generator

Generate structured `CHANGELOG.md` from git history using conventional commits.

## Setup

**Step 1:** Copy the script into your project:

```bash
cp scripts/generate-changelog.sh your-project/scripts/
```

**Step 2:** Run it:

```bash
cd your-project
bash scripts/generate-changelog.sh
```

**Step 3:** Review your new `CHANGELOG.md`:

```markdown
# Changelog

## [Unreleased]

### 🚀 Added
- New user dashboard (a1b2c3d)

### 🐛 Fixed
- Login redirect loop (e4f5g6h)
```

## Usage

### As a Claude Code Skill

1. Copy the `skills/changelog-generator/` folder into your `.claude/skills/` directory
2. In Claude Code, type: `/generate-changelog`
3. Claude will run the script and present the output

### As a CLI Script

```bash
# Bash version (zero dependencies)
bash scripts/generate-changelog.sh                    # Output to CHANGELOG.md
bash scripts/generate-changelog.sh --stdout            # Print to stdout
bash scripts/generate-changelog.sh --no-emoji          # Plain text output
bash scripts/generate-changelog.sh --output RELEASES.md # Custom filename

# Python version (zero dependencies)
python scripts/generate_changelog.py                   # Output to CHANGELOG.md
python scripts/generate_changelog.py --stdout           # Print to stdout
python scripts/generate_changelog.py --no-emoji         # Plain text
python scripts/generate_changelog.py --output RELEASES.md
```

### As a GitHub Action

Copy `.github/workflows/generate-changelog.yml` to your project. On every `v*` tag push, it auto-generates and commits a `CHANGELOG.md`.

## What It Does

1. Finds the latest git tag (sorted by version)
2. Fetches all commits since that tag
3. Parses conventional commit messages into 10 categories
4. Outputs a structured, human-readable CHANGELOG.md

## Conventional Commit Convention

| Prefix | Category | Emoji |
|--------|----------|-------|
| `feat:` | Added | 🚀 |
| `fix:` | Fixed | 🐛 |
| `refactor:` | Changed | 🔧 |
| `docs:` | Documentation | 📖 |
| `perf:` | Performance | ⚡ |
| `test:` | Testing | 🧪 |
| `security:` | Security | 🔒 |
| `build:`, `ci:` | Dependencies | 📦 |
| `revert:`, `remove:` | Removed | 🔥 |

## Files

```
├── scripts/
│   ├── generate-changelog.sh          # Bash implementation
│   └── generate_changelog.py          # Python implementation
├── skills/
│   └── changelog-generator/
│       └── SKILL.md                   # Claude Code skill
├── .github/workflows/
│   └── generate-changelog.yml         # GitHub Action
└── sample/
    └── CHANGELOG.md                   # Example output
```

## Requirements

- git 2.0+
- bash 4+ **or** python 3.6+

Created for the [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty) — Issue [#1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1).
