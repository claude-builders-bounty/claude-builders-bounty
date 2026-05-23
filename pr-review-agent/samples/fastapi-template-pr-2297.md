## PR Review

### Summary of changes
This PR updates repository documentation and security policy wording. The changed files are Markdown-oriented, so the main review focus should be accuracy, formatting, and whether the policy language matches current project practice.
Source reviewed: `https://github.com/fastapi/full-stack-fastapi-template/pull/2297`.

### Changed files
- Documentation/security policy files

### Identified risks
- Security policy changes can alter how users report vulnerabilities; verify contact details and supported-version language carefully.
- Documentation-only changes can still break rendered anchors or tables if Markdown formatting is invalid.

### Improvement suggestions
- Preview the rendered Markdown before merge.
- Ask a maintainer familiar with the vulnerability-reporting process to confirm the wording.
- Keep the PR description aligned with the final policy change so reviewers can verify intent quickly.

### Confidence score: Medium

