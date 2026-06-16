# Sample Outputs From Real GitHub PRs

Generated on 2026-06-16 with:

```bash
claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2827 --output samples/claude-builders-2827.md
claude-review --pr https://github.com/python/cpython/pull/151541 --output samples/cpython-151541.md
```

## Sample 1: claude-builders-bounty/claude-builders-bounty#2827

Source PR: https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2827

```markdown
## Claude PR Review

### Summary of changes
This review inspected https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2827 across 2 changed file(s): HOOK-README.md, block-destructive.sh. The parsed diff contains 96 added line(s) and 0 removed line(s), with emphasis on tests, configuration changes, and risky code patterns.

### Identified risks
- Source code changed without matching test files in the diff.
- Potentially risky pattern `rm -rf` appears in `HOOK-README.md`.
- Potentially risky pattern `DROP TABLE` appears in `HOOK-README.md`.
- Potentially risky pattern `rm -rf` appears in `block-destructive.sh`.
- Potentially risky pattern `DROP TABLE` appears in `block-destructive.sh`.

### Improvement suggestions
- Add or update tests that exercise the changed source paths before merging.
- Audit the flagged risky lines manually and add guardrails or input validation where applicable.
- Include a short manual verification note in the PR so reviewers can reproduce the result.
- Keep the final review comment focused on merge-blocking issues first, then non-blocking improvements.

### Changed files
- `HOOK-README.md`
- `block-destructive.sh`

### Confidence score: Low
```

## Sample 2: python/cpython#151541

Source PR: https://github.com/python/cpython/pull/151541

```markdown
## Claude PR Review

### Summary of changes
This review inspected https://github.com/python/cpython/pull/151541 across 3 changed file(s): Lib/email/contentmanager.py, Lib/test/test_email/test_contentmanager.py, Misc/NEWS.d/next/Library/2026-06-09-12-00-00.gh-issue-150771.K7mNx2.rst. The parsed diff contains 46 added line(s) and 1 removed line(s), with emphasis on tests, configuration changes, and risky code patterns.

### Identified risks
- No obvious high-risk pattern was found in the parsed diff (Lib/email/contentmanager.py, Lib/test/test_email/test_contentmanager.py, Misc/NEWS.d/next/Library/2026-06-09-12-00-00.gh-issue-150771.K7mNx2.rst).

### Improvement suggestions
- Run the touched test suite and include the exact command/output in the PR conversation.
- Keep the final review comment focused on merge-blocking issues first, then non-blocking improvements.

### Changed files
- `Lib/email/contentmanager.py`
- `Lib/test/test_email/test_contentmanager.py`
- `Misc/NEWS.d/next/Library/2026-06-09-12-00-00.gh-issue-150771.K7mNx2.rst`

### Confidence score: High
```
