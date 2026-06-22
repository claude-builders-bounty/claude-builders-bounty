# claude-review

A Claude Code agent that reviews GitHub PRs and returns structured Markdown feedback.

## What it does

Given a PR URL, `claude-review`:
1. Fetches the PR diff via `gh` CLI
2. Sends it to Claude for analysis
3. Returns a structured review with summary, risks, suggestions, and confidence score

## Setup

### Prerequisites

- Python 3.9+
- [GitHub CLI (`gh`)](https://cli.github.com/) — authenticated
- One of:
  - **Anthropic API key** (for API engine) — set `ANTHROPIC_API_KEY`
  - **Claude Code** installed (for claude-code engine)

### Install

```bash
cd claude-review
pip install .
```

Or run directly without installing:

```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123
```

## Usage

```bash
# Using the Anthropic API (default)
claude-review --pr https://github.com/owner/repo/pull/123

# Using Claude Code CLI (no API key needed)
claude-review --pr https://github.com/owner/repo/pull/123 --engine claude-code

# Save review to a file
claude-review --pr https://github.com/owner/repo/pull/123 -o review.md
```

## Output format

```markdown
# PR Review: owner/repo#123 — Fix login bug

## Summary
This PR fixes an authentication bypass in the login flow...

## Risks
- The token expiry logic may not handle edge cases
- No migration needed but existing sessions should be invalidated

## Suggestions
- Add rate limiting to the new endpoint
- Consider using a constant-time comparison for token validation

## Confidence
High
```

## Sample reviews

Tested on 2 real PRs from `anthropics/claude-code`:

### PR #69916 — fix: print error message before silent exit
```markdown
## Summary
This PR adds an error message to edit-issue-labels.sh when called without arguments.
Previously, the script would silently exit with code 1.

## Risks
- The error message goes to stderr (>&2), which is correct behavior
- No risk of breaking existing functionality

## Suggestions
- Consider adding a usage hint in the error message

## Confidence
High
```

### PR #69727 — fix(hookify): match file rules against Write tool content
```markdown
## Summary
This PR fixes a bug where file content matching didn't work for the Write tool.
The _extract_field method now correctly falls back to the content field.

## Risks
- Minimal change, well-scoped
- Preserves backward compatibility with Edit tool inputs

## Suggestions
- Add a unit test for Write tool field extraction

## Confidence
High
```

Full sample outputs: [`examples/`](examples/)

## Running tests

```bash
pip install pytest
pytest tests/
```

## License

MIT
