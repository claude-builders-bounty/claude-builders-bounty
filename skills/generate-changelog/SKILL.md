---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a project's git history since the last tag. Use when the user asks for a changelog, release notes, or asks to run /generate-changelog.
---

# Generate Changelog

Build a Keep-a-Changelog style `CHANGELOG.md` from git history using the
bundled `changelog.sh` script.

## Usage

```bash
bash changelog.sh [--output FILE] [--since TAG] [--repo PATH]
```

Or invoke this skill as `/generate-changelog`.

## What it does

1. Finds the most recent git tag (`git describe --tags --abbrev=0`);
   falls back to full history when the repo has no tags. (Note: the tag
   is the most recent reachable one and may come from another branch's
   history — `tag..HEAD` then means "commits not reachable from that tag".)
2. Collects non-merge commits in `<tag>..HEAD`.
3. Auto-categorizes each commit subject:
   - `feat:` / `feature:` → **Added** (conventional-commit prefix wins)
   - `fix:` / `bugfix:` / `hotfix:` → **Fixed**
   - `BREAKING CHANGE` / `feat!:` → **Changed**
   - otherwise keyword fallback (in this priority order): *fix/bug/patch*
     → **Fixed**; *add/new/implement/support* → **Added**;
     *remov/delet/drop/deprecat* → **Removed**; everything else → **Changed**
4. Writes grouped Markdown (`### Added` / `### Fixed` / `### Changed` /
   `### Removed`) with short hashes, newest first.

## Setup (3 steps)

Works with bash 3.2+ (including the bash shipped with macOS) — no
dependencies beyond git.

1. Copy `changelog.sh` into your project (or keep it on `PATH`).
2. `chmod +x changelog.sh`
3. `bash changelog.sh` — writes `./CHANGELOG.md`. A relative `--output`
   is resolved against the directory where you run the command.

## For the agent

When the user asks for a changelog or release notes, run the script with
the Bash tool from this skill's directory:

    bash "<skill-dir>/changelog.sh" [--output FILE] [--since TAG] [--repo PATH]

- `--repo` selects the target git repository; `--output` is relative to
  your current working directory.
- After generating, summarize the grouped sections for the user and give
  the file path; don't dump the whole file unprompted when it's long.

## Example

```bash
$ bash changelog.sh --since v1.2.0 --output CHANGELOG.md
wrote CHANGELOG.md (23 commits from v1.2.0 → HEAD)
```
