### Summary of Changes
This pull request introduces a pre-tool-use hook script (`pre-tool-use.py`) designed to block destructive bash commands from being executed by Claude Code. The hook scans requested terminal commands against a list of dangerous patterns (e.g., `rm -rf /`, `mkfs`, `dd`) using regex with word boundaries, logs blocked occurrences to `blocked.log`, and returns a cancellation error back to the runner.

### Identified Risks
- **Command Obfuscation Bypass**: Advanced command nesting, variable substitution, or base64 decoding in bash could potentially obfuscate destructive actions from basic regex matching.
- **Log Write Faults**: Writing directly to `blocked.log` in a read-only filesystem environment could raise an unhandled `IOError` and crash the hook runner itself, potentially blocking all subsequent tools.

### Improvement Suggestions
- **Robust Exception Handling**: Wrap the file logging logic in a try-except block to ensure that if `blocked.log` cannot be written, the script logs to stderr and still successfully returns the blocking payload rather than crashing.
- **Basic Shell Tokenizer**: Use Python's built-in `shlex` module to tokenize the command string before matching, ensuring that arguments and flags are parsed cleanly, avoiding regex false negatives or false positives.

### Confidence Score
**Score**: High
**Justification**: The hook is accompanied by a dedicated test suite with 6 diverse test cases covering critical word boundaries and edge cases, and it functions with zero external dependencies.
