# generate-changelog

A Claude Code skill and bash script that generates a structured `CHANGELOG.md` from git history using [Conventional Commits](https://www.conventionalcommits.org/) and [Keep a Changelog](https://keepachangelog.com/) format.

## Setup (3 steps)

1. **Copy the skill into your project:**
   ```bash
   cp -r skills/generate-changelog /path/to/your-project/.claude/skills/
   ```

2. **Use it in Claude Code:**
   ```
   /generate-changelog
   ```

3. **Or run the bash script directly:**
   ```bash
   bash changelog.sh
   ```

## How it works

The tool reads your git history, classifies each commit by its conventional commit prefix, and outputs a clean `CHANGELOG.md`:

| Commit prefix | Changelog section |
|---------------|-------------------|
| `feat:`       | **Added**         |
| `fix:`        | **Fixed**         |
| `refactor:`, `perf:`, `chore:`, `docs:`, `style:`, `ci:`, `build:` | **Changed** |
| `revert:`, `remove:`, `deprecate:` | **Removed** |

Commits are grouped by git tags (version releases). Repos with no tags produce a single "Unreleased" section.

## CLI options

```
bash changelog.sh                  # writes CHANGELOG.md in current dir
bash changelog.sh --output FILE    # writes to a custom path
bash changelog.sh --stdout         # prints to stdout
bash changelog.sh --from TAG       # only include commits after TAG
bash changelog.sh --repo DIR       # run against a different repo
```

## Sample output

See [SAMPLE_CHANGELOG.md](./SAMPLE_CHANGELOG.md) for output generated against this repository.
