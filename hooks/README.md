# Claude Code Pre-Tool-Use Safety Hook

An automated security hook for Claude Code that intercepts and prevents dangerous operations.

## Intercepted Patterns
- Recursive force removal operations
- Unrestricted SQL DROP and TRUNCATE operations
- Forced git branch overwrites
- Unbounded SQL DELETE without WHERE clauses

## Installation
1. Copy hook to 
2. Mark executable: 

## Audit Logging
Blocked attempts are recorded in  with timestamp and command details.
