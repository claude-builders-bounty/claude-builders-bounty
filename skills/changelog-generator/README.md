# 📋 Changelog Generator

> A Claude Code skill + bash script that generates a structured `CHANGELOG.md` from git history.

Automatically categorizes commits into **Added** / **Fixed** / **Changed** / **Removed** sections following the [Keep a Changelog](https://keepachangelog.com/) format.

## Setup (3 steps)

### Option A: As a Claude Code Skill

1. Copy `skills/changelog-generator/` into your project
2. Restart Claude Code
3. Type `/generate-changelog` — done!

### Option B: Standalone Bash Script

1. Download `changelog.sh` to your project
2. Run `bash changelog.sh`
3. Check the generated `CHANGELOG.md`

## How It Works

1. **Detects the latest git tag** — if no tags exist, all commits are included
2. **Reads commit messages** — extracts the subject line of each commit
3. **Categorizes by prefix** — matches conventional commit prefixes (`feat:`, `fix:`, etc.)
4. **Generates CHANGELOG.md** — outputs a properly formatted file

### Categorization

| Category | Matching Prefixes |
|----------|-------------------|
| **Added** | `feat`, `add`, `new`, `implement`, `introduce`, `create`, `support` |
| **Fixed** | `fix`, `bugfix`, `patch`, `resolve`, `repair`, `correct`, `hotfix` |
| **Changed** | `refactor`, `update`, `change`, `modify`, `improve`, `enhance`, `perf`, `style`, `chore`, `docs`, `test`, `ci`, `build`, `bump`, `rename`, `move`, `migrate`, `adjust`, `optimize`, `upgrade` |
| **Removed** | `remove`, `delete`, `drop`, `deprecate`, `clean`, `strip`, `uninstall` |

Supports conventional commit scopes: `feat(auth): add login` → **Added**

## Example Output

See [SAMPLE_OUTPUT.md](./SAMPLE_OUTPUT.md) for a real-world example generated from this repository.

## Requirements

- Git repository with at least one commit
- Bash 4.0+ (macOS / Linux / WSL)

## License

MIT
