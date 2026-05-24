### Summary
This PR adds a pre-tool-use hook (`block-destructive.py`) intended to block destructive Bash commands such as `rm -rf` and `DROP TABLE`. It operates by parsing the `Bash` tool input from stdin and applying a set of regex patterns to detect and exit with an error if dangerous operations are found.

### Risks
- **Security Bypass via Obfuscation:** The primary risk is that the hook relies on simple regex matching (`rm -rf`, `DROP TABLE`). In bash, this is easily bypassed using quotes (`r""m -r''f /`), command substitution (`$(echo rm) -rf /`), or variables (`CMD=rm; $CMD -rf /`).
- **False Negatives:** Attackers can bypass the blacklist by using alternative flags or paths not caught by the hardcoded regex.
- **Limited Scope:** The regex does not account for `curl | bash` pipelines or fork bombs (`:(){ :|:& };:`), which are common destructive vectors.

### Suggestions
- **Adopt AST Parsing:** Replace regex matching with a robust Bash Abstract Syntax Tree (AST) parser like `bashlex` to accurately resolve command structures regardless of obfuscation.
- **Use an Allowlist:** Instead of maintaining an incomplete blacklist of destructive commands, consider an allowlist of strictly safe commands (`ls`, `echo`, `cat`).
- **Implement a Execution Wrapper:** For true security, wrap the shell execution in a kernel-level sandbox (like `bwrap`) with network restrictions and ephemeral filesystem execution.

### Confidence
High
