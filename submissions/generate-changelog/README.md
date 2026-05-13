# generate-changelog

A Claude Code skill and bash script that generates a structured `CHANGELOG.md` from git history.

## Setup (3 steps)

1. **Copy files** into your project:
   ```bash
   cp SKILL.md changelog.sh /path/to/your/project/
   chmod +x changelog.sh
   ```

2. **Use with Claude Code** — invoke `/generate-changelog` in any git repository.

3. **Or run directly**:
   ```bash
   bash changelog.sh
   ```

## Options

```bash
bash changelog.sh                        # From last tag to HEAD
bash changelog.sh --since v1.0.0         # From specific tag
bash changelog.sh --output CHANGES.md    # Custom output file
```

## How It Works

- Fetches all commits since the last git tag (or all if no tags exist)
- Auto-categorizes into **Added** / **Fixed** / **Changed** / **Removed** using:
  - Conventional Commit prefixes (`feat:`, `fix:`, `refactor:`, etc.)
  - Keyword fallback matching for non-conventional commits
- Outputs [Keep a Changelog](https://keepachangelog.com/) formatted markdown

## Sample Output

Tested on [asyncapi/cli](https://github.com/asyncapi/cli) — 346 commits since v2.0.0, see `SAMPLE_OUTPUT.md`.
