# Claude Builders Bounty — Automation Tools

A collection of automation utilities for Claude Code, each submitted as a bounty solution.

## Tools

### 1. 📝 Changelog Generator (`generate_changelog.py`)

A Python CLI that generates a structured `CHANGELOG.md` from git history.

```bash
# All commits (auto-prepends to existing CHANGELOG.md)
python generate_changelog.py

# Only commits since a specific tag
python generate_changelog.py --since-tag v1.0

# Auto-detect last tag (no flag needed)
python generate_changelog.py

# Custom version label and output file
python generate_changelog.py --version v2.0 --output RELEASE_NOTES.md

# Preview without writing
python generate_changelog.py --dry-run

# Point to a different repo
python generate_changelog.py --cwd /path/to/repo

# Custom repo URL for commit links (auto-detected by default)
python generate_changelog.py --repo-url https://github.com/owner/repo
```

**Features:**
- Auto-categorizes commits into `Added`, `Fixed`, `Changed`, `Removed`
- Supports Conventional Commits (`feat:`, `fix:`, `refactor:`, etc.)
- Falls back to keyword matching for non-conventional messages
- Auto-detects the last git tag
- Auto-detects repo URL from `git remote`
- Prepends to existing CHANGELOG.md (preserves history)
- Each entry includes subject, commit link (full SHA), author, and date
- Zero dependencies (stdlib only)

**Sample Output:**

```markdown
# Changelog

## [v3.2] - 2026-05-27

### Added
- Add Excel export support ([fd96446](https://github.com/owner/repo/commit/fd964...full...sha)) by *Qiu-Difeng* on 2026-05-27

### Fixed
- Fix datetime import conflict ([fd96446](link)) by *Qiu-Difeng* on 2026-05-27

### Changed
- Update README with badges ([755ac79](link)) by *Qiu-Difeng* on 2026-05-27
```

---

### 2. 🔍 PR Review Agent (`bounties/bounty-4-pr-review-agent/`)

An AI-powered PR review CLI and GitHub Action that analyzes pull requests for risks and improvement suggestions.

**CLI Usage:**
```bash
# Review a PR by URL
node bounties/bounty-4-pr-review-agent/claude-review.js \
  --pr https://github.com/owner/repo/pull/123 \
  --token $GITHUB_TOKEN

# Review by owner/repo/number
node bounties/bounty-4-pr-review-agent/claude-review.js \
  --owner owner --repo repo --pr-number 123
```

**GitHub Action:**

See `bounties/bounty-4-pr-review-agent/github-action.yml` — automatically reviews new PRs and posts a structured comment with:
- Risk assessment (HIGH/MEDIUM/LOW)
- Improvement suggestions
- Confidence score

**Features:**
- Native Node.js HTTPS requests (no curl dependency)
- Full pagination support for large PRs
- Clean stdout output (diagnostics go to stderr)
- Shell-injection-safe argument handling

## License

MIT License
