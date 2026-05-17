## PR Review: Add changelog generation skill

Source: https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1528

### Summary

This PR appears to implement: Add changelog generation skill. The diff touches 4 file(s), led by skills/generate-changelog/changelog.sh, skills/generate-changelog/sample-output.md, skills/generate-changelog/README.md, skills/generate-changelog/SKILL.md. It adds 277 line(s) and removes 0 line(s). The review below is based on static diff inspection, so runtime behavior and project-specific intent still need maintainer confirmation.

### Changed Files

- `skills/generate-changelog/README.md`: +36 / -0 across 1 hunk(s)
- `skills/generate-changelog/SKILL.md`: +36 / -0 across 1 hunk(s)
- `skills/generate-changelog/changelog.sh`: +167 / -0 across 1 hunk(s)
- `skills/generate-changelog/sample-output.md`: +38 / -0 across 1 hunk(s)

### Identified Risks

- No major static risks found in the diff.

### Improvement Suggestions

- Check that documentation examples were run or at least smoke-tested.
- Add or reference tests that cover the main behavior introduced by this PR.

### Confidence

Medium
