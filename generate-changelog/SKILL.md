---
name: generate-changelog
description: Generate or update a structured CHANGELOG.md from git history since the last tag, auto-categorized Keep-a-Changelog style (Added / Changed / Deprecated / Removed / Fixed / Security). Use when the user asks to generate a changelog, draft release notes from commits, update CHANGELOG.md for a release, or summarize what changed since the last version.
---

# Generate Changelog

Produce a structured `CHANGELOG.md` section from the project's git history.
A deterministic bash script (`changelog.sh`, bundled next to this file) does
the parsing and formatting — always prefer it over hand-writing entries, so
the output is reproducible.

## Workflow

1. **Confirm the context.** Make sure the working directory is the project
   root of a git repository (`git rev-parse --git-dir`). If it is not a git
   repo, say so and stop.
2. **Pick the version.**
   - If the user named a version (e.g. "changelog for 1.4.0"), use it.
   - Otherwise default to an `Unreleased` section.
   - Never invent a version number.
3. **Run the script** (it lives beside this SKILL.md):

   ```bash
   bash "<skill-dir>/changelog.sh" --version <X.Y.Z>   # or omit --version for Unreleased
   ```

   Useful flags: `--all` (one section per tag, full history),
   `--from <ref>` / `--to <ref>` (explicit range), `--output <file>`,
   `--stdout` (preview without writing), `--overwrite` (regenerate).
4. **Show the result.** Print the generated section to the user and point at
   the updated `CHANGELOG.md`. If the script reports "no commits in range",
   relay that — do not pad the changelog with invented entries.
5. **Hands off the history.** The script never edits commits, tags, or an
   existing release section (it refuses a duplicate version heading on
   purpose). If the user wants changes to the wording, edit the generated
   section in `CHANGELOG.md` directly and say what you changed.

## How categorization works

- Conventional Commit prefixes are authoritative: `feat` → Added,
  `fix` → Fixed, `perf`/`refactor`/`docs`/`chore`/… → Changed,
  `security` → Security, `deprecate` → Deprecated, `remove` → Removed.
- Non-conventional subjects fall back to first-word keyword rules
  ("Add …", "Fixed …", "Remove …", …), defaulting to Changed.
- `!` markers and `BREAKING CHANGE:` footers prefix an entry with
  **BREAKING:**.
- Merge commits, bare version subjects, and duplicate entries are skipped.
- Compare links (`[1.4.0]: …/compare/v1.3.0...v1.4.0`) are emitted when an
  `origin` remote exists; pass `--repo-url` to override.

## Fallback: if changelog.sh is unavailable

Do the same job manually: run
`git log --no-merges --pretty=format:'%s%n%b%x1e' <last-tag>..HEAD`
(find the last tag with `git describe --tags --abbrev=0`), categorize each
subject with the rules above, and format the section exactly as:

```markdown
## [Unreleased]

### Added

- Entry text, scope shown as **scope:** prefix when present
```

Keep the categories in this order and omit empty ones:
Added, Changed, Deprecated, Removed, Fixed, Security.
