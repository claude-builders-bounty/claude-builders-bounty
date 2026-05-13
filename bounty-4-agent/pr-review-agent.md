# PR Review Agent
Claude Code sub-agent that reviews PR diffs.

## Usage
claude-code --agent pr-review -- "gh pr view 123"

## Review Criteria
- Correctness, Security, Performance, Maintainability

## Output Format
Markdown with severity: Critical/Warning/Suggestion
