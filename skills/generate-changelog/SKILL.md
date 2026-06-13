---
name: generate-changelog
description: "Generate a structured CHANGELOG.md from git history with automatic categorization (Added/Fixed/Changed/Removed)"
version: 1.0.0
author: Hermes Agent / comunidad Claude Builders
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [changelog, git, documentation, automation, release]
    category: documentation
---

# Generate CHANGELOG Skill

Automatically generates a structured `CHANGELOG.md` from your project's git history. Categorizes commits into **Added**, **Fixed**, **Changed**, **Removed** based on conventional commit messages.

## Quick Start (3 Steps)

```bash
# 1. Copy this skill to your project's .claude/skills/ (or any path)
cp -r generate-changelog /path/to/your/project/.claude/skills/

# 2. Run the generator
bash /path/to/your/project/.claude/skills/generate-changelog/scripts/changelog.sh

# 3. Review and commit CHANGELOG.md
git add CHANGELOG.md && git commit -m "docs: update changelog"
```

Or use as a Claude Code slash command: `/generate-changelog`

---

## Features

| Feature | Description |
|---------|-------------|
| **Auto-categorization** | Parses conventional commits → Added / Fixed / Changed / Removed |
| **Tag-based range** | Generates changelog since last git tag (or all history if no tags) |
| **Multiple formats** | Outputs Markdown (default), JSON, or plain text |
| **Customizable** | Configurable categories, commit prefix patterns, output path |
| **Zero dependencies** | Pure bash + standard Unix tools (git, awk, sed) — no Python/Node required |
| **CI/CD ready** | Exit codes for automation, works in GitHub Actions/GitLab CI |

---

## Installation

### Option A: As a Claude Code Skill (Recommended)

```bash
# In your project root
mkdir -p .claude/skills
cp -r /path/to/generate-changelog .claude/skills/
```

Then use in Claude Code: `/generate-changelog`

### Option B: Standalone Script

```bash
# Download the script directly
curl -sSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/skills/generate-changelog/scripts/changelog.sh \
  -o changelog.sh && chmod +x changelog.sh
```

---

## Usage

### Basic (generates since last tag)

```bash
bash scripts/changelog.sh
```

### Custom output file

```bash
bash scripts/changelog.sh -o docs/CHANGELOG.md
```

### Full history (ignore tags)

```bash
bash scripts/changelog.sh --all
```

### Specific version range

```bash
bash scripts/changelog.sh --from v1.0.0 --to v2.0.0
```

### JSON output for tooling

```bash
bash scripts/changelog.sh --format json > changelog.json
```

### Dry run (preview without writing)

```bash
bash scripts/changelog.sh --dry-run
```

---

## Commit Convention

The skill uses **Conventional Commits** to categorize changes:

| Prefix | Category | Example |
|--------|----------|---------|
| `feat:` / `feature:` | **Added** | `feat: add user authentication` |
| `fix:` / `bugfix:` | **Fixed** | `fix: resolve login redirect loop` |
| `refactor:` / `perf:` / `style:` | **Changed** | `refactor: simplify auth middleware` |
| `remove:` / `del:` / `delete:` | **Removed** | `remove: deprecated API v1` |
| `docs:` / `chore:` / `ci:` / `test:` / `build:` | *Ignored* | (metadata commits) |

Commits without recognized prefix fall under **Changed**.

---

## Configuration (Optional)

Create `.changelogrc` in your project root:

```ini
# .changelogrc
[output]
path = CHANGELOG.md
format = markdown

[categories]
custom_added = feat,feature,add
custom_fixed = fix,bugfix,hotfix
custom_changed = refactor,perf,style,improve
custom_removed = remove,del,delete

[git]
# Custom tag pattern (default: v*)
tag_pattern = v*
# Commit range (default: last tag..HEAD)
range = auto
```

---

## Example Output

```markdown
# CHANGELOG

## [v2.1.0] - 2026-06-13

### Added
- Add user authentication with JWT tokens
- Add OAuth2 integration for Google/GitHub login

### Fixed
- Fix login redirect ignoring ?next= parameter
- Fix memory leak in WebSocket connection handler

### Changed
- Refactor auth middleware for cleaner error handling
- Improve password hashing from SHA256 to Argon2id

### Removed
- Remove deprecated API v1 endpoints

---

## [v2.0.0] - 2026-05-01

### Added
- Initial release with core features
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/changelog.yml
name: Generate Changelog
on:
  push:
    tags: ['v*']
jobs:
  changelog:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Generate Changelog
        run: |
          bash scripts/changelog.sh
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          body_path: CHANGELOG.md
```

### Pre-commit Hook (optional)

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: changelog
      name: Update changelog on version bump
      entry: bash scripts/changelog.sh
      language: system
      files: 'package\.json$|pyproject\.toml$|Cargo\.toml$'
```

---

## How It Works

1. **Detects last tag** — `git describe --tags --abbrev=0` (or uses `--from`)
2. **Fetches commits** — `git log <range> --pretty=format:"%h|%s|%b"`
3. **Categorizes** — Matches commit subject against prefix patterns
4. **Formats** — Groups by category, writes Markdown with version header
5. **Outputs** — Writes to `CHANGELOG.md` (or custom path)

---

## Testing the Skill

Test on this very repo:

```bash
cd /path/to/claude-builders-bounty
bash skills/generate-changelog/scripts/changelog.sh --dry-run
```

Expected: Shows commits since last tag categorized correctly.

---

## Contributing

PRs welcome! See [CONTRIBUTING.md](../../CONTRIBUTING.md) if it exists.

1. Fork the repo
2. Create feature branch: `git checkout -b feat/my-improvement`
3. Make changes, test locally
4. Submit PR with clear description

---

## License

MIT — Free to use, modify, distribute.

---

## Credits

Created for the **Claude Builders Bounty** community. Powered by [Opire](https://opire.dev) for bounty management.