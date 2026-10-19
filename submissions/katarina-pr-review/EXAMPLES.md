# Example PR review outputs (manual, not Claude API execution)

These two examples were prepared by reading actual public unified diffs. The API-backed CLI has not been exercised with an Anthropic key in this submission; these are transparent qualitative examples, **not evidence of a live execution**.

## Example 1 — https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4810

### Summary
Adds a dependency-free changelog generator that groups reachable non-merge commits by conventional-commit prefixes and escapes Markdown content. The accompanying README and tests document its behavior and existing-file overwrite rules.

### Risks
- Commit-subject heuristics cannot infer the semantic category of unconventional messages; this is documented rather than a correctness guarantee.
- The README describes running Git fetch manually, so a shallow checkout will fail without the operator first fetching full history.

### Suggestions
- Add a fixture containing malformed/unusual commit subjects and shell metacharacters to demonstrate safe output.
- In the PR discussion, provide a concise statement of which integration checks have and have not been run.

### Confidence
**Medium** (static diff review; no runtime execution).

## Example 2 — https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4834

### Summary
Adds a Python PreToolUse guard for selected destructive commands and an installer that merges the Bash hook into existing Claude settings. Tests and documentation explain the scope and intentionally conservative policy.

### Risks
- The recursive scanner shown in the diff recognizes a nested shell when the flag token is precisely -c; combined forms such as bash -lc may need separate handling.
- The installer writes the settings JSON directly after taking a backup; an interrupted write can leave an incomplete settings file even though a backup exists.

### Suggestions
- Exercise bash -lc, env bash -c and multiple quoted shell-wrapper cases in adversarial tests, documenting residual bypasses.
- Atomically replace the settings file using a temporary file in the same directory.

### Confidence
**Medium** (static diff review; no runtime execution).

The examples contain only publicly visible repository information, not secrets.
