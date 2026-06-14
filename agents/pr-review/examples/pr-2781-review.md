## 🤖 Claude Review: [BOUNTY $100] HOOK: Pre-tool-use hook that blocks destructive bash commands

### Summary
This PR adds `hooks/pre-tool-use/blocker.py`, a Claude Code pre-tool-use hook that intercepts dangerous bash commands (`rm -rf`, `DROP TABLE`, `git push --force`, etc.) before they execute. It logs blocked attempts to a file and displays clear messages explaining the block. A README with 2-command install is included.

### Identified Risks
- **risk: Python import complexity** — The hook imports `datetime`, `json`, `os`, `re`, `sys`, `timezone` on every invocation. For a pre-tool-use hook that fires before every Claude Code tool call, this adds ~20-30ms of overhead each time. This is minor but could be optimized by restructuring as a single self-contained script with lazy imports.
- **risk: UTF-8 edge cases in command parsing** — If a command contains non-UTF-8 characters (unlikely in typical development but possible with piped binary data), `sys.stdin.read()` will raise. Adding `errors='replace'` to the read call would protect against this.

### Improvement Suggestions
- **suggestion: Allow per-project overrides via config file** — Currently, all customization requires editing `DESTRUCTIVE_PATTERNS` in the script. Supporting a `~/.claude/hooks/blocker-config.json` would let users whitelist specific commands per project without forking the hook.
- **suggestion: Add `git push --force --force-with-lease` ambiguity handling** — The SAFE_OVERRIDES allow `--force-with-lease` but many users type `git push --force` out of habit. Consider auto-suggesting `--force-with-lease` in the block message rather than just logging it.
- **suggestion: Test for `chmod -R 777` on non-root paths** — The current pattern only blocks `chmod -R 000 /` and `chmod -R 000 /`. `chmod -R 777 /etc` would not be caught. Consider broadening to block recursive chmod on common system directories.

### Confidence Score
**High** — The hook is well-structured, handles the core requirements cleanly, and the regex patterns are properly scoped to avoid false positives on safe commands.
