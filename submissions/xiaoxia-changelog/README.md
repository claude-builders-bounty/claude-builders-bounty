# CHANGELOG Generator Skill

Generates a structured `CHANGELOG.md` from git commit history using conventional commit prefixes.

## Quick Start (2 commands)

```bash
curl -O https://raw.githubusercontent.com/YOUR_USER/claude-builders-bounty/main/submissions/xiaoxia-changelog/changelog.sh
chmod +x changelog.sh
./changelog.sh
```

## Usage

```bash
./changelog.sh [output-file] [since-tag] [repo-url]

# Examples:
./changelog.sh                                     # default: CHANGELOG.md, all commits
./changelog.sh CHANGELOG.md v1.0.0                 # commits since v1.0.0
./changelog.sh docs/CHANGELOG.md v0.5.0 https://github.com/user/repo  # with commit links
```

## Features
- Auto-detects commits since last git tag
- Categorizes by conventional commit prefixes (feat:, fix:, refactor:, security:, etc.)
- Groups into Added / Fixed / Changed / Removed / Security / Other
- Optional commit hash links when repo URL provided
- Deduplicates entries automatically
