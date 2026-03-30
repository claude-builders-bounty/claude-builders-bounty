# Claude Code PR Review Agent

This is a standalone Sub-Agent that uses the Anthropic `claude-code` CLI and GitHub API to automatically review Pull Requests. It takes a PR URL as input, fetches the diff, and returns a structured Markdown review comment.

## Setup Requirements

1. Install Claude Code (must be in your PATH): `npm install -g @anthropic-ai/claude-code`
2. Authenticate Claude Code: `claude login`
3. Install standard Python requirements:
```bash
pip install requests
```

*(Optional)* Export `GITHUB_TOKEN` to avoid public API rate limits.

## Usage

Run the agent via CLI on any public PR:

```bash
python3 claude-review.py --pr https://github.com/owner/repo/pull/123
```

## Example Output

```markdown
### Summary
Refactored the database initialization layer to handle asynchronous connections gracefully. Switched to `psycopg3` natively and added a fallback embedded string loader.

### Identified Risks
- Unhandled `OperationalError` possible if the database is unreachable on boot.
- The `init_schema()` sequence removes robust transactions on initial table generation.

### Improvement Suggestions
- Wrap the schema initialization within an `async with conn.transaction():` context.
- Inject a timeout parameter to prevent indefinite hangs.

### Confidence Score
High
```
