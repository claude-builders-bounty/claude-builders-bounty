# CHANGELOG Generator — Issue #1

Generate a structured `CHANGELOG.md` from git history, auto-categorized into Added / Fixed / Changed / Removed sections.

## Setup (3 steps)

```bash
# 1. Copy the script
cp changelog.sh /usr/local/bin/generate-changelog
chmod +x /usr/local/bin/generate-changelog

# 2. Run in any git repo
cd your-project
generate-changelog

# 3. Done — check CHANGELOG.md
cat CHANGELOG.md
```

Or without installing:
```bash
bash changelog.sh
```

## Usage

```bash
bash changelog.sh                        # auto-detects last tag, writes CHANGELOG.md
bash changelog.sh --since v1.2.3         # start from a specific tag
bash changelog.sh --output HISTORY.md    # write to a different file
bash changelog.sh --dry-run              # print to stdout, don't write file
```

## Claude Code Skill

Copy `SKILL.md` to your Claude commands directory:

```bash
mkdir -p ~/.claude/commands/generate-changelog
cp changelog.sh SKILL.md ~/.claude/commands/generate-changelog/
# Then in Claude Code:
# /generate-changelog
# /generate-changelog --since v1.0.0 --dry-run
```

## What it produces

```markdown
## v1.3.1 — 2026-03-29

> Changes since `v1.3.0`. 14 commit(s) total.

### Added
- feat: add dark mode toggle ([a1b2c3d](https://github.com/owner/repo/commit/a1b2c3d...))

### Fixed
- fix: resolve memory leak in event handler ([e4f5g6h](https://github.com/owner/repo/commit/e4f5g6h...))

### Changed
- refactor: extract authentication middleware ([i7j8k9l](https://github.com/owner/repo/commit/i7j8k9l...))

### Removed
- remove: drop support for Node.js 16 ([m0n1o2p](https://github.com/owner/repo/commit/m0n1o2p...))
```

See [sample-output.md](sample-output.md) for real examples from actual repos.

## Auto-categorization rules

| Commit prefix | Category |
|---------------|----------|
| `feat`, `add`, `implement`, `new` | Added |
| `fix`, `bug`, `patch`, `resolve` | Fixed |
| `remove`, `delete`, `drop`, `deprecat` | Removed |
| Everything else | Changed |

## Features

- Works on any git repository
- Auto-detects last tag to set `since` range
- Infers next version from last tag (e.g. `v1.2.3` → `v1.2.4`)
- SHA links point to GitHub/GitLab if a remote URL is configured
- Merge commits excluded automatically
- Works with **bash 3.2+** (macOS default) and bash 4/5+
- Zero dependencies — pure bash + git
