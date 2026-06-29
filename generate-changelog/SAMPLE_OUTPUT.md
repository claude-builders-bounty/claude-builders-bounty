# Sample Output

This sample uses real commit subjects from the public `xxCodexIAxx/claude-builders-bounty` branch `bounty/generate-changelog-1782694130` after the solution files were published. It demonstrates the same category mapping used by `generate-changelog/changelog.sh`.

```markdown
# Changelog

All notable changes to `claude-builders-bounty` are documented in this file.

Generated on 2026-06-29 from commits for HEAD~8..HEAD.

## [Unreleased] - 2026-06-29

### Added

- initial README with bounty board (1aeae2a)
- Add changelog.sh (9970cf8)
- Add generate-changelog/changelog.sh (3ca0f5f)
- Add generate-changelog/SKILL.md (5735deb)
- Add generate-changelog/README.md (d843cd2)
- Add generate-changelog/SAMPLE_OUTPUT.md (1d5bb91)

### Changed

- Initial commit (a80a580)

```

Local execution note: this Codex Windows sandbox exposes only the WSL launcher for `bash` and has no `git` binary available, so the branch was verified through the GitHub API here. On a normal repository with Git and Bash installed, run `bash changelog.sh --range HEAD~8..HEAD` to reproduce the same format.
