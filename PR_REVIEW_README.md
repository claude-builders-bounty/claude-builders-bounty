# Claude Code PR Review Agent

A CLI agent that reviews GitHub PRs using Claude and posts structured feedback.

## Setup

```bash
chmod +x pr-review-agent.sh
export ANTHROPIC_API_KEY="sk-ant-..."
gh auth login  # if not already authenticated
```

## Usage

```bash
# Review a PR (prints to stdout)
./pr-review-agent.sh facebook/react 28000

# Review and post as PR comment
POST_COMMENT=true ./pr-review-agent.sh owner/repo 123
```

## Output Format

```markdown
## Summary
Brief overview of changes.

## Strengths
- Well-structured code
- Good test coverage

## Issues
- [ ] **Critical**: SQL injection in user input handler
- [ ] **Warning**: Missing error handling in API call
- [ ] **Suggestion**: Consider extracting helper function

## Security
No security concerns found.

## Verdict
APPROVE | REQUEST_CHANGES | COMMENT
```

## Requirements
- `gh` CLI (authenticated)
- `curl`, `jq`
- `ANTHROPIC_API_KEY` environment variable

Closes #4
