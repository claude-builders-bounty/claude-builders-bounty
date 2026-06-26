## Claude Review

### Summary
This PR changes 5 file(s) with 273 additions and 0 deletions. It primarily touches 3 docs files, 2 source files. The stated goal is: Add generate changelog skill.

### Changed files reviewed
- `.gitattributes`
- `generate-changelog/README.md`
- `generate-changelog/SAMPLE_OUTPUT.md`
- `generate-changelog/SKILL.md`
- `generate-changelog/changelog.sh`

### Identified risks
- Source files changed without obvious test files in the diff.
- Destructive-operation wording appears in the diff; confirm safeguards and tests cover it.

### Improvement suggestions
- Add or reference tests that exercise the main behavior changed by this PR.
- Keep the PR description aligned with the final files and validation commands.

### Confidence score
Medium
