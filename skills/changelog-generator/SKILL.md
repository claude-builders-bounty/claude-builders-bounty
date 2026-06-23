# Changelog Generator Skill

Generate a structured `CHANGELOG.md` from a project's git history.

## Usage

```bash
# Generate CHANGELOG.md in current directory
./changelog.sh

# Specify output file
./changelog.sh --output docs/CHANGELOG.md

# Generate for another repo
./changelog.sh --repo /path/to/project
```

Or as a Claude Code / OpenClaw skill command:

```
/generate-changelog
```

## How It Works

1. Detects the last git tag (or uses the initial commit if no tags exist)
2. Iterates through commits grouped by tag
3. Categorizes each commit message:
   - `feat:` → **Added**
   - `fix:` → **Fixed**
   - `docs:` → **Documentation**
   - `refactor:`, `perf:`, `test:`, `chore:`, `style:`, `ci:`, `build:` → **Changed**
   - `revert:`, `remove`, `delete` → **Removed**
4. Falls back to keyword matching for non-conventional messages
5. Outputs a clean, structured Markdown file

## Requirements

- `bash` 4+ (for associative arrays)
- `git`
- No external dependencies

## Files

- `changelog.sh` — The main script
- `README.md` — Setup and usage instructions
