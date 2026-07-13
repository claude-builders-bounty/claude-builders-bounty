# changelog-gen — Structured CHANGELOG from Git History

Generates a [Keep a Changelog](https://keepachangelog.com/) format `CHANGELOG.md` from conventional commits.

## Quick Start (3 steps)

```bash
# 1. Clone or copy the changelog-generator directory into your project
# 2. Run it:
bash changelog-generator/changelog.sh --version 1.0.0 --output CHANGELOG.md
# 3. Done. Check CHANGELOG.md
```

## Usage

```bash
# Generate since last tag, print to stdout
bash changelog-generator/changelog.sh

# With version label and file output
bash changelog-generator/changelog.sh --version 1.2.0 --output CHANGELOG.md

# Append to existing CHANGELOG.md (prepends new content)
bash changelog-generator/changelog.sh --version 1.2.0 --append --output CHANGELOG.md

# Link commits to GitHub
bash changelog-generator/changelog.sh --github owner/repo --output CHANGELOG.md

# Since a specific tag
bash changelog-generator/changelog.sh --since v0.9.0 --version 1.0.0

# Or use Python directly
python3 changelog-generator/changelog_gen.py --version 1.0.0
```

## What it does

1. Reads `git log` since the last tag (or `--since` ref)
2. Parses conventional commits (`feat:`, `fix:`, `chore:`, etc.)
3. Categorizes into: **Added** / **Fixed** / **Changed** / **Removed**
4. Highlights breaking changes with **BREAKING** prefix
5. Links commit hashes to GitHub (with `--github`)

## Conventional commit mapping

| Prefix | Category |
|--------|----------|
| `feat:` | Added |
| `fix:` | Fixed |
| `perf:`, `refactor:`, `docs:`, `chore:`, `style:`, `build:`, `ci:`, `test:` | Changed |
| `revert:` | Removed |
| `feat!:` or `BREAKING CHANGE` in body | Changed (**BREAKING**) |

Non-conventional commits are categorized as **Changed**.

## Sample Output

Generated from [anthropics/anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python):

```markdown
## [0.40.0] - 2026-07-13

### Added

- **api:** add agent-memory-2026-07-22 beta header ([`4253c06`](https://github.com/anthropics/anthropic-sdk-python/commit/4253c06))
- **api:** add support for Managed Agents event delta streaming ([`d1a933e`](https://github.com/anthropics/anthropic-sdk-python/commit/d1a933e))
- **api:** add support for claude-sonnet-5 ([`ab10964`](https://github.com/anthropics/anthropic-sdk-python/commit/ab10964))
- **api:** add support for 20260318 web fetch and support tools ([`5849d19`](https://github.com/anthropics/anthropic-sdk-python/commit/5849d19))
- **client:** add support for system.message streaming events ([`0868a68`](https://github.com/anthropics/anthropic-sdk-python/commit/0868a68))

### Changed

- **api:** remove some nonfunctional types from the SDKs ([`5385af6`](https://github.com/anthropics/anthropic-sdk-python/commit/5385af6))
- **docs:** updates to descriptions and example values ([`ced24a0`](https://github.com/anthropics/anthropic-sdk-python/commit/ced24a0))
- **api:** remove retired models from API and SDKs ([`37a7d36`](https://github.com/anthropics/anthropic-sdk-python/commit/37a7d36))

### Fixed

- **agent_toolset:** allow absolute paths that resolve inside workdir ([`8a004a2`](https://github.com/anthropics/anthropic-sdk-python/commit/8a004a2))
- async count_tokens missing output_format/output_config merge block ([`f212547`](https://github.com/anthropics/anthropic-sdk-python/commit/f212547))
- **memory tool:** create parent directories with the correct permissions ([`97d3d9b`](https://github.com/anthropics/anthropic-sdk-python/commit/97d3d9b))
```

## Options

| Flag | Description |
|------|-------------|
| `--since REF` | Git ref to start from (default: last tag) |
| `--version`, `-v` | Version label (e.g., `1.2.0`) |
| `--date DATE` | Release date (default: today) |
| `--github OWNER/REPO` | Link commits to GitHub |
| `--output`, `-o` | Write to file instead of stdout |
| `--append` | Prepend to existing CHANGELOG.md |

## Requirements

- Python 3.8+ (stdlib only)
- Git repository
- Conventional commits (recommended but not required)

## As a Claude Code Skill

Copy `SKILL.md` to your Claude Code skills directory. Then use `/generate-changelog` in Claude Code.
