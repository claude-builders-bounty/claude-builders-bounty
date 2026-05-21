# Changelog Generator Skill

Generate a structured `CHANGELOG.md` from git history — works as a Claude Code skill or standalone bash script.

## Setup (3 steps)

1. **Copy the skill files** into your project:
   ```bash
   cp changelog.sh /path/to/your/project/
   cp SKILL.md /path/to/your/project/.claude/skills/
   ```

2. **Run it:**
   ```bash
   bash changelog.sh
   ```
   Or in Claude Code: type `/generate-changelog`

3. **Done.** A `CHANGELOG.md` appears in your repo root.

## What It Does

- Fetches commits since the last git tag (or all history if no tags)
- Auto-categorizes using conventional commit prefixes:
  - `feat:` → **Added**
  - `fix:` → **Fixed**
  - `refactor:`, `chore:`, `docs:`, etc. → **Changed**
  - `remove:` → **Removed**
- Falls back to keyword matching for non-conventional commits
- Outputs a clean, formatted `CHANGELOG.md`

## Options

| Flag | Description |
|------|-------------|
| `--tag <tag>` | Generate changelog since a specific tag |
| `--all` | Include all history |
| `-o <file>` | Custom output file (default: `CHANGELOG.md`) |

## Example

```bash
bash changelog.sh --tag v1.0.0 -o RELEASE_NOTES.md
```

## Compatibility

- Bash 4+ (macOS, Linux, WSL)
- No external dependencies (pure git + bash)
- Works with any conventional commit format
