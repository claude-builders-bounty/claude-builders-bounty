# Code Review — claude-builders-bounty/claude-builders-bounty#351

> **Reviewed with:** `claude-review --pr claude-builders-bounty/claude-builders-bounty/351`

---

## Summary

This PR adds a zero-dependency bash script (`changelog.sh`) that generates a
categorised `CHANGELOG.md` from git history, plus a Claude Code skill file
(`SKILL.md`) that exposes it as a `/generate-changelog` slash command.
Categorisation is keyword-based (conventional commits supported), the script is
idempotent (prepends new sections), and all options are surfaced via clean CLI flags.

## Identified Risks

- **Logic / Medium** — The categorisation relies on substring matching against commit
  subject lines with no precedence order. A commit like `fix: remove deprecated auth`
  contains both `fix:` (→ Fixed) and `remove` (→ Removed). Whichever branch is
  evaluated first wins, which may produce surprising output. Explicit precedence
  (feat > fix > remove > change) would make the behavior deterministic.
  _Affected:_ `skills/changelog/changelog.sh`

- **Data / Low** — `--since` accepts any string and passes it directly to
  `git log --since="$SINCE"`. An argument like `--since "$(rm -rf ~)"` is a
  command injection vector if the script is ever called from a web UI or CI
  with user-controlled input. Validate that `$SINCE` matches a tag/date pattern
  before interpolation.
  _Affected:_ `skills/changelog/changelog.sh`

- **Logic / Low** — The `--dry-run` flag prints to stdout but the script also
  writes progress messages to stdout (not stderr). In pipelines
  (`bash changelog.sh --dry-run | downstream-tool`) the progress messages will
  be mixed into the CHANGELOG content. Route progress/status messages to stderr.

## Improvement Suggestions

1. **Support `--format keep-scope`** — conventional commits like `fix(auth): ...`
   currently strip `fix(auth):` entirely. Many teams want the scope preserved:
   `(auth) correct null pointer when config is missing`. A flag to control this
   would widen adoption.

2. **Add a `--tag` flag that creates a git tag after writing the CHANGELOG** —
   the natural follow-up action after generating `## [v1.1.0]` is
   `git tag v1.1.0`. Rolling this into the script eliminates a manual step and
   is consistent with how `npm version` and `standard-version` work.

3. **SKILL.md trigger list is incomplete** — users who type "update changelog" or
   "what changed since last release" won't activate the skill. Add aliases:
   ```markdown
   - Update the changelog
   - What changed since the last release?
   - Create release notes
   ```

4. **The README sample output uses placeholder hashes** — `a1b2c3d`, `e4f5g6h`, etc.
   Using real hashes from this repo (even from the bounty repo's own history) would
   make the example more credible and testable.

## Confidence Score

**High** — Focused, self-contained change with clear scope. The identified risks are
mostly edge cases in adversarial or pipeline contexts, not problems for the typical
interactive use case.
