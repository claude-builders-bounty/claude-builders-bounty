---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a repository's git history. Use when the user asks for a changelog, release notes, or "what changed since the last release". Categorises commits into Added / Changed / Fixed / Removed, is idempotent, and never overwrites existing history.
---

# /generate-changelog

Turn git history into a Keep-a-Changelog-shaped \`CHANGELOG.md\`.

## When to use

- "write me a changelog", "what changed since v1.2.0", "draft release notes"
- After a release, to record what landed since the last tag.

## How to invoke

\`\`\`bash
bash changelog.sh                                     # since the last tag
bash changelog.sh --from <ref> --version <x.y.z>      # explicit range and heading
bash changelog.sh --out <path>                        # write elsewhere
\`\`\`

If the repository has no tags, the script falls back to the root commit so the first run is never empty.

## Output contract

\`\`\`markdown
## [1.3.0] - YYYY-MM-DD

### Added
- <commit subject without prefix>  (<short sha>)

### Changed
- ...

### Fixed
- ...

### Removed
- ...
\`\`\`

Empty sections are omitted entirely. If nothing landed in the range, the section body is a single italic line saying so.

## Rules the script guarantees

1. **Idempotent**: a second run over the same range prints \`already up to date\` and exits 0; it never duplicates a heading.
2. **Non-destructive**: an existing \`CHANGELOG.md\` is prepended with the new section, old content preserved.
3. **Loud failures**: outside a git repo, or with an unknown \`--from\` ref, it exits non-zero with a message rather than writing a partial file.
4. **Deterministic categorisation**, no model call: prefix match on the commit subject, scopes stripped.

## Categorisation table

| Prefix | Section |
| --- | --- |
| feat, feature, add, new | Added |
| fix, bugfix, hotfix, patch | Fixed |
| remove, delete, drop, deprecat | Removed |
| everything else | Changed |

Unconventional subjects land in Changed rather than being dropped — the script never silently discards a commit.

## Verification

\`\`\`bash
bash tests/run-tests.sh    # 11 checks, exits non-zero on failure
\`\`\`

## Limits

- Merge commits are skipped unless \`--include-merges\` is passed.
- No semantic-version inference: pass \`--version\` when you want a real number instead of \`Unreleased\`.
- No issue/PR link generation; the repo's remote is not consulted.
