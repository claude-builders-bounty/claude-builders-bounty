# CHANGELOG Generator Skill

Automatically generates a structured `CHANGELOG.md` from a project's git history.

## Quick Start

```bash
# 1. Copy to your project
cp -r skills/changelog-generator/ your-project/.claude/skills/changelog-generator/

# 2. Make executable
chmod +x your-project/.claude/skills/changelog-generator/changelog.sh

# 3. Run it
cd your-project && .claude/skills/changelog-generator/changelog.sh -o CHANGELOG.md
```

## Usage

```bash
# Since last tag (auto-detected) → stdout
./changelog.sh

# Since specific tag
./changelog.sh --from-tag v1.0.0

# Write to file
./changelog.sh -o CHANGELOG.md

# Custom range
./changelog.sh --from-tag v1.0.0 --to-ref main -o CHANGELOG.md
```

## How It Works

1. **Detects the last git tag** (or uses `--from-tag`)
2. **Fetches all commits** since that tag via `git log`
3. **Categorizes each commit** by keyword matching:
   - `Added` — feat, add, new, implement, create, introduce
   - `Fixed` — fix, bug, patch, hotfix, resolve, close
   - `Changed` — change, update, modify, refactor, improve, tweak, adjust
   - `Removed` — remove, delete, deprecate, drop
   - `Other` — everything else
4. **Outputs a formatted Markdown** file with sections for each category

## Output Format

```markdown
# Changelog

## v1.0.0 → 2026-09-04 (42 commits)

### Added
- **feat: add user authentication** (2026-09-03, John)

### Fixed
- **fix: resolve login redirect loop** (2026-09-02, Jane)

### Changed
- **refactor: extract auth module** (2026-09-01, John)

---
*Generated on 2026-09-04 by changelog.sh*
```

## Tips

- **Conventional Commits** give the best categorization accuracy
- Run in CI/CD on release to auto-generate changelogs
- The script is pure bash — no dependencies beyond `git`
