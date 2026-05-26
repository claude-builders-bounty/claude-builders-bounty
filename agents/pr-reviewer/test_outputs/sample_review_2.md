### Summary of Changes
This pull request adds a git history changelog generator skill. It introduces a shell script (`changelog.sh`) and a Claude Code skill description (`SKILL.md`) that retrieves all commits since the last git release tag, parses them by conventional commit prefixes, categorizes them into Keep-a-Changelog sections (Added, Fixed, Changed, Removed), and updates the repository's `CHANGELOG.md`.

### Identified Risks
- **No Tag Fallback**: If the repository lacks any tags, the `git describe --tags --abbrev=0` command will fail with a non-zero exit status, which could crash the script or result in an empty list of commits.
- **Unconventional Commit Formats**: Commit messages that do not follow conventional naming formats are grouped into a generic `Changed` section, which may lead to cluttered formatting in repositories with mixed styles.

### Improvement Suggestions
- **Fallback Logic**: Add a check to detect if no tags exist in the repository, and fall back to retrieving all commits from the repository's root commit or the last 100 commits.
- **Output Cleanup**: Trim whitespaces, commit hashes, and author names cleanly to produce a highly readable output format.

### Confidence Score
**Score**: High
**Justification**: The script correctly utilizes standard git commands and conventional patterns, and it has been verified to run successfully on active git logs.
