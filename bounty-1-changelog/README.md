# changelog.sh — Generate CHANGELOG.md from git history

A bash script that automatically generates a structured `CHANGELOG.md` from a project's git history, following the [Keep a Changelog](https://keepachangelog.com/) format and [Conventional Commits](https://www.conventionalcommits.org/) specification.

## Setup (3 steps)

```bash
# 1. Download the script
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/bounty-1-changelog/changelog.sh

# 2. Make it executable
chmod +x changelog.sh

# 3. Run it
bash changelog.sh
```

Done — `CHANGELOG.md` is created in your project root.

## Usage

```bash
# Full history (all tags + unreleased)
bash changelog.sh

# From a specific tag to HEAD
bash changelog.sh v1.2.0

# Between two specific tags
bash changelog.sh v1.1.0 v1.2.0

# Custom output file
bash changelog.sh -o RELEASES.md
```

## How It Works

1. Reads all git tags sorted by version (oldest → newest)
2. For each tag range, fetches non-merge commits
3. Auto-categorizes commits based on conventional-commit prefixes:

| Prefix | Category |
|--------|----------|
| `feat:` | **Added** |
| `fix:` | **Fixed** |
| `refactor:`, `perf:`, `docs:`, `style:`, `test:`, `chore:`, `ci:`, `build:` | **Changed** |
| `remove:` | **Removed** |
| `deprecate:` | **Deprecated** |
| `feat!:`, `fix!:`, or `BREAKING CHANGE` footer | **Removed** |

4. Outputs a properly formatted `CHANGELOG.md` with versions, dates, and categorized entries

## Claude Code Skill

A `SKILL.md` is also included — copy it to your `.claude/skills/` directory to enable the `/generate-changelog` command in Claude Code.

## Requirements

- Bash 4.0+
- Git

## Sample Output

See [SAMPLE_OUTPUT.md](./SAMPLE_OUTPUT.md) for an example generated from a real repository.

## License

MIT
