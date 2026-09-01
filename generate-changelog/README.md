# Generate Changelog

A lightweight bash script that generates a structured `CHANGELOG.md` from your project's git history. It parses [Conventional Commits](https://www.conventionalcommits.org/) and auto-categorizes entries into **Added**, **Fixed**, **Changed**, and **Removed**.

## Quick Start (3 Steps)

1. **Download** `changelog.sh` into your project:
   ```bash
   curl -sL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/generate-changelog/changelog.sh -o changelog.sh && chmod +x changelog.sh
   ```

2. **Run** it in your git repository:
   ```bash
   bash changelog.sh
   ```

3. **Check** the generated `CHANGELOG.md`:
   ```bash
   cat CHANGELOG.md
   ```

## Usage

```bash
bash changelog.sh [OPTIONS]

Options:
  --from <tag>     Start from this git tag (default: last reachable tag)
  --to <ref>       End at this ref (default: HEAD)
  --output <file>  Output file path (default: CHANGELOG.md)
  --repo <path>    Path to git repository (default: current directory)
  -h, --help        Show help
```

### Examples

```bash
# Generate changelog for the current repo (since last tag)
bash changelog.sh

# Generate from v1.0.0 to v2.0.0
bash changelog.sh --from v1.0.0 --to v2.0.0

# Output to a custom file
bash changelog.sh --output docs/CHANGELOG.md

# Run on a different repo
bash changelog.sh --repo /path/to/project
```

## How It Works

The script:
1. Finds the most recent git tag (or uses `--from` if specified)
2. Fetches all non-merge commits between that tag and `HEAD` (or `--to`)
3. Parses each commit message using Conventional Commits format
4. Categorizes entries:
   - `feat` / `add` → **Added**
   - `fix` / `hotfix` → **Fixed**
   - `refactor` / `perf` / `chore` / `docs` / `style` / `ci` → **Changed**
   - `remove` / `revert` / `deprecate` → **Removed**
5. Writes a formatted `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/)

### Conventional Commit Format

```
type(scope): description
```

| Type        | Category  |
|-------------|-----------|
| `feat`      | Added     |
| `fix`       | Fixed     |
| `refactor`  | Changed   |
| `remove`    | Removed   |

Breaking changes (e.g., `feat!:`) are marked with ⚠️ BREAKING.

## Requirements

- **Bash 4.0+** (for associative arrays)
- **Git** (any recent version)
- No other dependencies

## Claude Code Skill (Optional)

This project includes a `SKILL.md` file that allows [Claude Code](https://docs.anthropic.com/en/docs/claude-code) to invoke the changelog generator as a native skill. Place `SKILL.md` and `changelog.sh` in your `.claude/skills/generate-changelog/` directory.

## Sample Output

See `sample-CHANGELOG.md` for an example of the generated output.

## License

MIT
