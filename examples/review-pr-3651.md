# PR Review: claude-builders-bounty/claude-builders-bounty#3651

> Source: https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3651
> PR Title: feat: add generate-changelog skill (closes #1)
> Review generated: 2026-08-01T17:30:00Z
> Model: claude-3-5-sonnet-20241022

## Summary
This PR adds a `generate-changelog` skill for Claude Code. It includes a self-contained bash script (`changelog.sh`, 7.9 KB, zero external dependencies) that auto-generates a `CHANGELOG.md` from git history, plus a `SKILL.md` definition, README, and a SAMPLE_OUTPUT.md with verified test runs. The script is compatible with macOS, Linux, and Git Bash on Windows.

## Risks
- The script auto-bumps the semver patch version from the last git tag without confirmation — if a user accidentally runs it on a release branch with the wrong tag context, they could ship a wrong version. Consider adding a `--confirm` flag for production releases.
- The "added dark mode support" heuristic (without `feat:` prefix) lands in `Added` even if it's actually a refactor — heuristics are not perfect. False positives are mostly harmless but worth noting.
- The `awk` based version inference only handles strict semver (X.Y.Z). Tags like `v1.2.3-rc.1` would fall through to "Unreleased".

## Suggestions
- Add a `--dry-run` flag that prints the would-be section without writing the file
- Support a `.changelog-ignore` file (gitignore-style) to skip specific commits
- Add CI badge to README showing test status
- Consider supporting a config file (`.changelogrc`) for project-specific categorisation rules

## Confidence
**High** — The diff is well-structured, the script has a clear test suite (7/7 scenarios), and the documentation is comprehensive. The risks identified are concrete but minor.
