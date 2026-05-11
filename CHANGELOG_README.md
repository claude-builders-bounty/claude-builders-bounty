# 📋 Git Changelog Generator

Automatically generates a structured `CHANGELOG.md` from a project's git history.

## Setup (3 steps)

```bash
# 1. Download the script
curl -O https://raw.githubusercontent.com/508704820/claude-builders-bounty/feat/changelog-generator/changelog.sh

# 2. Make it executable
chmod +x changelog.sh

# 3. Run it in any git repo
./changelog.sh /path/to/your/repo
```

Or use as a Claude Code command — add to your `.claude/commands/`:

```
Generate a changelog: bash changelog.sh .
```

## How It Works

1. Detects the last git tag (or uses all commits if no tags exist)
2. Fetches all commits since that tag
3. Auto-categorizes each commit into:
   - **Added** — `feat`, `add`, `new`, `create`, `implement`, `introduce`, `support`
   - **Fixed** — `fix`, `bug`, `patch`, `resolve`, `close`, `repair`, `hotfix`
   - **Changed** — `refactor`, `update`, `improve`, `modify`, `rename`, `move`, `chore`, `build`, `ci`
   - **Removed** — `remove`, `delete`, `drop`, `deprecate`, `cleanup`, `revert`
   - **Other** — anything that doesn't match the above patterns
4. Supports [Conventional Commits](https://www.conventionalcommits.org/) prefixes
5. Generates clickable commit links (GitHub URL auto-detected)
6. Appends to existing CHANGELOG.md (preserves history)

## Sample Output

```markdown
# Changelog

## Unreleased (since v2.1.0) (2026-05-11)

### Added
- feat: add user authentication ([a1b2c3d](https://github.com/owner/repo/commit/a1b2c3d))
- new dashboard widget ([e4f5g6h](https://github.com/owner/repo/commit/e4f5g6h))

### Fixed
- fix: resolve login timeout on slow connections ([i7j8k9l](https://github.com/owner/repo/commit/i7j8k9l))

### Changed
- refactor: simplify config loading ([m0n1o2p](https://github.com/owner/repo/commit/m0n1o2p))
```

## Features

- ✅ Auto-detects last git tag
- ✅ Supports Conventional Commits (`feat:`, `fix:`, `refactor:`, etc.)
- ✅ Clickable GitHub commit links
- ✅ Preserves existing changelog sections
- ✅ No dependencies (bash + python3)
- ✅ Works on any git repo
