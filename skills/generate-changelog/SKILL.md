---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history. Use when the user asks to create or update a changelog, summarise recent commits, or run /generate-changelog.
---

# Generate Changelog

Generate a structured `CHANGELOG.md` from a project's git history, following
[Keep a Changelog](https://keepachangelog.com/) and the categories the
project asks for: `Added` / `Fixed` / `Changed` / `Removed`.

## When to use this skill

- The user runs `/generate-changelog` or asks for a changelog.
- A release is being prepared and recent commits need summarising.
- A repo has no changelog yet and one should be created from history.

## How it works

1. Find the starting point: the most recent reachable git tag
   (`git describe --tags --abbrev=0`). If the repo has no tags, use the
   full history. `--since <ref>` overrides this.
2. Read commits in `<since>..HEAD` with `git log` (record separator
   `\x1e`, field separator `\x1f`, so multi-line bodies are safe).
3. Classify every commit — first match wins, in this order:
   1. `BREAKING CHANGE` in the body, or `!` after the type (`feat!:`):
      category `Changed`, entry prefixed `⚠ BREAKING: `.
   2. Conventional-Commit type: `feat` → Added; `fix` / `security` →
      Fixed; `remove` / `delete` / `drop` / `deprecate` → Removed;
      `refactor` / `perf` / `chore` / `build` / `ci` / `docs` /
      `style` / `test` / `revert` / `change` / `update` / `bump` /
      `deps` → Changed.
   3. Free-text keywords, checked Removed → Fixed → Added → Changed,
      so "remove the fix" is not misfiled as a fix.
   4. Anything else → Changed. Nothing is silently dropped.
   5. `Merge ...` commits are skipped unless `--include-merges`.
   6. `Revert "..."` commits → Changed, kept as `Revert: <original>`.
   7. Exact duplicate subjects (case-insensitive) are de-duplicated.
   8. `type(scope): description` → `Description (scope)`, first letter
      capitalised, trailing `.` stripped.
4. Render Keep-a-Changelog Markdown. Only non-empty sections are emitted,
   in the order Added / Fixed / Changed / Removed. The section is labelled
   `Unreleased` by default (commits after a tag are, by definition,
   unreleased); `--version X.Y.Z` overrides the label.

## Usage

```bash
# From the skill directory (or copy the two files into your repo):
python3 generate_changelog.py                 # writes CHANGELOG.md
bash changelog.sh                             # same, via the wrapper
python3 generate_changelog.py --dry-run       # print to stdout
python3 generate_changelog.py --since v1.0.0  # explicit starting ref
python3 generate_changelog.py --version 1.2.0 --output docs/CHANGELOG.md
python3 generate_changelog.py --show-hashes   # append short SHAs
python3 generate_changelog.py --include-merges
```

Requirements: `python3` (3.8+) and `git`. No third-party packages.

## Edge cases

- No tags in the repo → all history is used, section is `Unreleased`.
- No commits since the last tag → a valid file is still written, stating
  `No changes since <tag>.`, and the command exits 0.
- Empty repository / not a git repo → a clear error on stderr, exit 1.

## Tests

```bash
python3 -m unittest discover -s tests -v   # 40+ tests, no pytest needed
python3 -m pytest tests/ -q                # also works, if pytest is installed
```

## Example output

See `SAMPLE_CHANGELOG.md` — generated from a real repository
(pallets/markupsafe, commits after its latest tag) with the command in
that file's header. The classification counts are printed when the tool
runs, e.g. `Wrote CHANGELOG.md (Unreleased, 12 entries, 14 commits
since v3.0.2).`
