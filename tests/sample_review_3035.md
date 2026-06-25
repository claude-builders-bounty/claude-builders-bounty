### Summary of Changes
This PR implements a pre-tool-use hook (`hooks/destructive_command_hook.py`) in Python that intercepts dangerous bash commands before they are executed by Claude Code. It blocks destructive actions like `rm -rf`, database deletions (`DROP TABLE`, `TRUNCATE`, `DELETE FROM` without `WHERE`), and force pushes (`git push --force`).

### Identified Risks
- **Over-blocking**: Normal utility commands (e.g. displaying help, running git diff) that happen to contain keywords like `DROP TABLE` or `DELETE` might get blocked. (Note: The author addressed this by checking for safe command prefixes like `echo`, `git diff`, and `cat`).
- **Python Execution Latency**: Since the hook runs on every tool execution, spawning a Python interpreter might add small latency to tool calls compared to a pure Bash script.

### Improvement Suggestions
- **Configuration Verification**: Add a verification command to help users test that the hook is active and blocking successfully.
- **Log Rotation**: Implement log rotation or limit log size for `blocked.log` to prevent it from growing indefinitely over long-term usage.

### Confidence Score
**High** - The implementation is clean, includes a zero-dependency script, has a complete test suite with edge cases, and logs all attempts reliably.
