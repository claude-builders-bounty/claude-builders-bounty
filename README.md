# Changelog Generator

Generate a structured `CHANGELOG.md` from your git history — auto-categorizes commits into **Added / Fixed / Changed / Removed**.

## Setup (3 steps)

1. **Clone or copy** `changelog.sh` into your repo
2. **Make it executable:** `chmod +x changelog.sh`
3. **Run it:** `bash changelog.sh`

That's it! 🎉

## Usage

```bash
# Basic — generates CHANGELOG.md from last tag
bash changelog.sh

# Since a specific tag
bash changelog.sh --since-tag v1.0.0

# Custom output file
bash changelog.sh --output CHANGES.md
```

## How It Works

1. Finds the last git tag (or all commits if no tags)
2. Fetches commits since that tag
3. Categorizes by conventional commit prefix:
   - `feat:`, `add:`, `new:`, `create:`, `implement:` → **Added**
   - `fix:`, `bugfix:`, `patch:`, `resolve:`, `correct:` → **Fixed**
   - `refactor:`, `update:`, `improve:`, `change:`, `chore:` → **Changed**
   - `remove:`, `delete:`, `drop:`, `deprecate:` → **Removed**
   - Everything else → **Other**
4. Outputs a formatted `CHANGELOG.md`

## Claude Code Skill

Drop `SKILL.md` into your `.claude/skills/` directory to use via `/generate-changelog`.

## Requirements

- `git`
- `bash 4+`

## Sample Output

See [sample-output.md](sample-output.md) — generated from a real repo with 775+ commits.

## License

MIT
