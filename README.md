# Changelog Skill — Generate structured CHANGELOG.md from git history

A Claude Code skill (plus standalone bash script) that generates a structured `CHANGELOG.md` from a project's git history.

## What it does

- Fetches all commits since the **last git tag** (or the first commit if no tags exist)
- Auto-categorizes commit subjects into **Added / Fixed / Changed / Removed**
- Writes a properly formatted `CHANGELOG.md` (Keep a Changelog style)

## Setup (2 steps)

1. Copy this folder into your project (contains `SKILL.md`, `changelog.sh`, `README.md`)
2. Make the script executable:

   ```bash
   chmod +x changelog.sh && ./changelog.sh
   ```

That's it. Run `./changelog.sh` after every release to regenerate the changelog.

## Usage

| Command | Effect |
|---|---|
| `./changelog.sh` | Generate from last tag → `CHANGELOG.md` |
| `./changelog.sh v1.2.0` | Generate since tag `v1.2.0` |
| `./changelog.sh v1.2.0 release-notes.md` | Custom output file |

In Claude Code, you can also ask: *"generate changelog"* — the skill handles it automatically.

## Categorization rules

| Category | Commit prefixes (case-insensitive) |
|---|---|
| **Added** | `add`, `new`, `feature`, `feat`, `implement`, `introduce`, `initial`, `create`, `support` |
| **Fixed** | `fix`, `bug`, `resolve`, `patch`, `repair`, `hotfix`, `correct`, `revert` |
| **Removed** | `remove`, `delete`, `drop`, `deprecat`, `cleanup` |
| **Changed** | `change`, `update`, `refactor`, `improve`, `rewrite`, `migrate`, `rename`, `bump`, `upgrade`, `enhance`, `perf`, `docs`, `chore`, `style`, `build`, `ci`, `test` |
| **Other** | anything else |

## Sample output

See `sample-output.md` for a changelog generated from a real repository.

## Requirements

- Git
- Bash (any POSIX shell works; on Windows use Git Bash / WSL)
