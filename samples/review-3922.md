## Summary
This PR introduces a changelog generation skill with two duplicate implementations (root-level and `skills/generate-changelog/`), including bash scripts that parse git commits and produce a `CHANGELOG.md`. It also adds initial documentation (`SKILL.md`) and a sample changelog entry.

## Identified Risks
- **Duplicate implementations**: Two nearly identical `changelog.sh` scripts exist at different paths (`./changelog.sh` and `skills/generate-changelog/changelog.sh`), creating confusion about which to use and maintenance overhead.
- **Inconsistent categorization logic**: The root `changelog.sh` uses broad grep patterns (`feat|add|new`) while the skills version uses stricter `case` matching on `feat:` or `feat(`, leading to different outputs depending on which script runs.
- **Missing "Changed" category in root script's SKILL.md**: The root `SKILL.md` documents four categories but the table doesn't include all prefixes handled by the script (e.g., `change`, `refactor`, `update`, `improve` are mentioned but not clearly mapped).
- **No handling of empty commit ranges**: If there are no commits since the last tag, the scripts still output a version header with empty sections, which may be undesirable.
- **Hardcoded output path in skills version**: `skills/generate-changelog/changelog.sh` always writes to `CHANGELOG.md` in the repo root regardless of the input path argument, which could overwrite unexpected files.
- **Date uses system locale**: `date +%Y-%m-%d` depends on system timezone, potentially producing inconsistent dates across environments.

## Improvement Suggestions
- **Consolidate to a single implementation**: Remove one of the duplicate `changelog.sh` + `SKILL.md` pairs, or make one a thin wrapper around the other to avoid drift.
- **Standardize commit parsing**: Use a consistent convention (e.g., Conventional Commits with `type(scope): message`) across both scripts, and document supported prefixes clearly in `SKILL.md`.
- **Add guard for empty diffs**: Skip writing the changelog file or output a warning if no commits are found in the range.
- **Make output path explicit**: Allow the skills version to respect the `$REPO_DIR` argument when writing `CHANGELOG.md`, or document that it always writes to the repo root.
- **Pin timezone for reproducibility**: Use `TZ=UTC date +%Y-%m-%d` or document that the date reflects the local system timezone.
- **Add tests or examples**: Include sample commit messages and expected output in `SKILL.md` to clarify behavior.

## Confidence Score
High
