# Claude Code PR Reviewer Agent

A Python-based CLI agent that leverages the Anthropic API (Claude) to automatically review GitHub Pull Requests. It analyzes the PR diff and provides a structured Markdown review.

## Prerequisites

- Python 3.8+
- GitHub CLI (`gh`) installed and authenticated
- An Anthropic API key

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Export your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

3. Make the script executable (optional):
   ```bash
   chmod +x claude-review
   ```

## Usage

Run the agent via CLI by passing the GitHub PR URL:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

You can also specify a different model or token limit:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --model claude-sonnet-5-20250728 --max-tokens 4096
```

### Sample Output

```markdown
### Summary of Changes
This pull request introduces a new automated CLI validation feature in the `packages/effect/src/unstable/cli/internal/command.ts` file. It prevents the system from silently ignoring excess positional arguments by raising an `UnrecognizedArgument` error when extra parameters are provided.

### Identified Risks
- The change might break existing integrations that accidentally pass trailing flags or parameters and rely on the silent ignoring behavior.
- Users relying on the previous behavior without variadic parameters will start seeing immediate errors upon upgrading.

### Improvement Suggestions
- Consider adding a configuration flag to enable/disable strict argument parsing for backward compatibility.
- Ensure that the generated help docs explicitly specify whether a command accepts extra trailing arguments.

### Confidence Score
High
```
