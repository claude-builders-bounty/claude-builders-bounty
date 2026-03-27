# Generate Changelog — Claude Code Skill

A Claude Code skill that generates a structured `CHANGELOG.md` from a project's git history.

## Setup (3 steps)

1. **Copy** `skills/generate-changelog/changelog.sh` into your project (or add it to your PATH)
2. **Run it**: `bash changelog.sh`
3. **Done** — `CHANGELOG.md` is written to your project root

## Usage

### Bash Script

```bash
# Generate changelog since last tag (auto-detected)
bash changelog.sh

# Output to custom file
bash changelog.sh -o RELEASE_NOTES.md

# Include all commits (no tag filtering)
bash changelog.sh -a

# Specify a starting tag
bash changelog.sh -t v1.0.0

# Target a different repo
bash changelog.sh -r /path/to/repo
```

### Claude Code

Just ask: *"Generate a changelog from git history"* and Claude will invoke the script.

## How It Works

Commits are auto-categorized by prefix into five groups:

| Category | Matching prefixes |
|----------|-------------------|
| **Added** | `feat`, `add`, `new`, `implement` |
| **Fixed** | `fix`, `bug`, `patch`, `resolve`, `close` |
| **Changed** | `change`, `update`, `refactor`, `improve`, `modify`, `chore`, `perf` |
| **Removed** | `remove`, `delete`, `deprecate`, `drop` |
| **Other** | Everything else |

## Sample Output

See `SAMPLE_OUTPUT.md` for a real-world example generated from the [commander.js](https://github.com/tj/commander.js) repository.

## Requirements

- Bash 4+
- Git
- No external dependencies
