---
name: generate-changelog
description: Generate a structured Keep-a-Changelog CHANGELOG.md from git history since the last tag. Use when the user asks for a changelog, release notes, or runs /generate-changelog.
argument-hint: "[--since TAG] [--output FILE] [--repo PATH]"
disable-model-invocation: false
allowed-tools: Bash(python3 *) Bash(bash *) Bash(git *)
---

# Generate Changelog

Build a Keep-a-Changelog style `CHANGELOG.md` from the current repository's git history using the bundled generator (Python 3 stdlib only + a bash entrypoint).

## Quick start

```bash
bash ${CLAUDE_SKILL_DIR}/changelog.sh
```

Or invoke this skill directly as `/generate-changelog`.

## What it does

1. Resolves the start ref: `--since TAG` if given, otherwise the latest git tag (`git describe --tags --abbrev=0`), otherwise full history.
2. Collects non-merge commits in `<tag>..HEAD`.
3. Auto-categorizes each subject into **Added** / **Fixed** / **Changed** / **Removed**:
   - Conventional Commits win first (`feat:`, `fix:`, `feat(api)!:`, `docs:`, …).
   - Free-text heuristic fallback (priority: Fixed → Added → Removed → Changed).
   - Breaking markers (`!` or `BREAKING CHANGE`) are flagged and land under **Changed**.
4. Writes (or `--prepend`s) a properly formatted `CHANGELOG.md`. Commit subjects are printed literally — never executed.

## Setup (3 steps)

1. Copy `skills/generate-changelog/` into `~/.claude/skills/generate-changelog/` (or into the project `.claude/skills/`).
2. `chmod +x changelog.sh scripts/generate.py`
3. From any git repo: `bash ~/.claude/skills/generate-changelog/changelog.sh`

Requires `git` and `python3`. No pip packages.

## CLI

```bash
bash changelog.sh [--output FILE] [--since TAG] [--repo PATH] [--title TITLE] [--prepend] [--dry-run]
```

| Flag | Meaning |
|------|---------|
| `--output` / `-o` | Output path (default `CHANGELOG.md`, relative to CWD) |
| `--since` | Start tag/ref (default: latest tag) |
| `--repo` | Target git repository (default `.`) |
| `--title` | Section heading title (default `Unreleased`) |
| `--prepend` | Insert the new `##` section into an existing changelog |
| `--dry-run` | Print to stdout only |

## For the agent

When the user asks for a changelog or release notes:

1. Run from this skill directory (or via `${CLAUDE_SKILL_DIR}`):

   ```bash
   bash "${CLAUDE_SKILL_DIR}/changelog.sh" --repo . --output CHANGELOG.md
   ```

2. Summarize the four sections for the user; do not dump a huge file unprompted.
3. If they want release notes for a specific tag range, pass `--since <prev-tag>` and `--title <version>`.

## Example

```text
$ bash changelog.sh --repo /path/to/commander.js --since v13.1.0 --title 14.0.0
wrote CHANGELOG.md (31 commits from v13.1.0 → HEAD)
```

See [examples/sample-CHANGELOG.md](examples/sample-CHANGELOG.md) for real output from [tj/commander.js](https://github.com/tj/commander.js) (`v13.1.0` → `v14.0.0`).
