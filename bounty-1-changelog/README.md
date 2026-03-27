# generate-changelog

Automatically generate a structured `CHANGELOG.md` from your git history. Commits are categorized into **Added**, **Fixed**, **Changed**, and **Removed** using conventional commit prefixes or keyword matching.

## Setup (3 steps)

**1. Copy the files into your project:**

```bash
cp changelog.sh /path/to/your/repo/
cp SKILL.md /path/to/your/repo/.claude/skills/generate-changelog/SKILL.md
```

**2. Make the script executable:**

```bash
chmod +x changelog.sh
```

**3. Run it:**

```bash
# As a standalone script
bash changelog.sh

# Or as a Claude Code slash command
/generate-changelog
```

## How It Works

The script reads `git log` since the most recent tag and categorizes each commit:

| Commit style | Example | Category |
|---|---|---|
| Conventional prefix | `feat: add dark mode` | Added |
| Conventional prefix | `fix: null pointer in auth` | Fixed |
| Keyword fallback | `Update dependencies` | Changed |
| Keyword fallback | `Remove legacy API` | Removed |

Merge commits are excluded. Unmatched commits default to **Changed**.

## Output Format

The output follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/):

```markdown
# Changelog

All notable changes to **my-project** are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Unreleased - 2026-03-26

### Added
- Add user authentication endpoint (`a1b2c3d`)
- Implement rate limiting (`d4e5f6a`)

### Fixed
- Fix memory leak in WebSocket handler (`b7c8d9e`)

### Changed
- Update Node.js to v22 (`f0a1b2c`)
```

## Flags

| Flag | Description |
|---|---|
| `--all` | Full changelog across every tag |
| `--since <ref>` | Changelog from a specific tag or commit |
| `--output <file>` | Custom output filename (default: `CHANGELOG.md`) |
| `--dry-run` | Print to stdout, do not write a file |
| `--help` | Show usage information |

## Requirements

- Git
- Bash 4.0+

## License

MIT
