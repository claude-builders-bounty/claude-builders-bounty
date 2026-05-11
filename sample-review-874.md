## PR Review Summary

This PR, `Add destructive Bash command blocker hook`, changes 3 file(s) with 246 additions and 0 deletions. Primary touched files: hooks/README.md, hooks/block_destructive_bash.py, hooks/test_block_destructive_bash.py. This automated review focuses on diff metadata, changed file patterns, and common risk signals.

## Identified Risks

- Diff includes destructive command/database patterns; verify guardrails and explicit intent.

## Improvement Suggestions

- Run the project's narrowest relevant test/lint command before merge and include the result in the PR.
- Confirm the PR description explains user-visible behavior, validation performed, and any known limitations.
- For documentation changes, verify links, commands, and examples against the current repository layout.

## Confidence Score

**High**
