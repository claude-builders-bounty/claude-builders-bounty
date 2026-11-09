---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a project's git history. Use when the user asks to create, update, or regenerate a changelog, prepare release notes, summarize commits since the last tag, or document what changed between versions. Do not use for publishing releases, npm publishing, or writing marketing announcements.
license: MIT
compatibility: Requires git and bash (Linux, macOS, WSL); no other dependencies.
---

# Generate Changelog

Generate a `CHANGELOG.md` from git history, categorized per Keep a Changelog:
`Added` / `Fixed` / `Changed` / `Removed`.

## When to use

- "Write/update a changelog" or "release notes for the upcoming version"
- "What changed since the last tag?"
- Preparing a release PR or documenting a milestone

## When not to use

- Publishing a release to a registry (npm/pypi) — that is the release tooling's job
- Generating a changelog for a repo without git history (write it manually)

## Workflow

1. Run the bundled script — it is deterministic and handles edge cases:

   ```bash
   bash scripts/changelog.sh [since-ref]
   ```

   - `since-ref` (optional): a tag, branch, or commit. Defaults to the most recent
     reachable tag (`git describe --tags --abbrev=0`).
   - Writes `CHANGELOG.md` to the repo root, or prints to stdout when output is piped.

2. Read the generated output and verify sections make sense. The script buckets
   commits by Conventional Commits prefixes (`feat:`, `fix:`, `chore:`, `refactor:`,
   `perf:`, `docs:`, `test:`, `build:`, `ci:`, `style:`) and keyword fallback
   ("add", "fix", "remove", "refactor", "improve", "update", "bump", "drop").
   Move misplaced entries by hand if the heuristics guessed wrong.

3. Fill the version header if the user knows the next version, otherwise keep
   `Unreleased` (that is what the script writes).

4. If a `CHANGELOG.md` already exists, the script **prepends** the new section and
   keeps prior content. Do not regenerate history — changelogs are append-only.

## Common edge cases (the script handles these)

- **No tags yet**: falls back to the repo's first commit, logs a note on stderr.
- **No commits since the tag**: exits with a clear message, writes nothing.
- **Merge squashes / "Merge branch 'x'" commits**: skipped, they carry no unique info.
- **Piped output** (`changelog.sh | cat`): prints to stdout instead of writing the file.
  Pass `--stdout` to force printing, or set `CL_FORCE_FILE=1` in CI to force the file.
- **Existing CHANGELOG.md**: new section prepended, old content preserved.

## Gotchas

- `git describe` needs at least one tag; on tagless repos the script uses the root commit.
- Commit subjects longer than 100 chars are truncated — long subjects usually mean
  the body holds the real message; check `git log` if an entry looks cut off.
- On Windows, run from WSL or Git Bash; the script is POSIX bash.
