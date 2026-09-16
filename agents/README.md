# Claude Code PR Reviewer Agent

A Claude Code sub-agent that analyzes a GitHub PR diff and outputs a structured Markdown review including summary, risks, improvement suggestions, and confidence score.

## Features
- CLI execution via `claude-review --pr <URL>`
- Automated diff fetching from GitHub API
- Security scanning (detects unsafe execution patterns, hardcoded secrets)
- Structured Markdown output (Summary, Risks, Suggestions, Confidence score)
- Tested on real GitHub PRs

## Quick Setup & Usage

1. **Prerequisites**: Python 3.8+
2. **Run review**:
   ```bash
   python3 agents/pr_reviewer.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3848
   ```

## Output Format Example
```markdown
## PR Review Summary
- **Summary**: PR introduces changes across 3 file(s) with 150 additions and 0 deletions.
- **Confidence**: High

### Identified Risks
- No high-severity security risks or anti-patterns detected in diff.

### Improvement Suggestions
- Small, focused PR. Good for incremental improvements.
- Code structure is clean. Ensure unit tests pass before merging.
```

## Testing
Tested against pull requests #3848, #3849, and #3850 on `claude-builders-bounty/claude-builders-bounty`. Outputs verified.

## File Structure
```
agents/
└── pr_reviewer.py    # Main sub-agent script
```

## License
MIT