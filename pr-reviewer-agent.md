# PR Reviewer Agent

A JavaScript agent that reviews pull requests and generates structured Markdown output with summary, risks, nitpicks, and verdict sections.

## Features

- ✅ Verifies issue state is OPEN and not already rewarded before processing
- 📋 Generates structured Markdown output with:
  - Summary (title, author, files changed, lines added/removed)
  - Risks (potential issues with the PR)
  - Nitpicks (minor improvements)
  - Verdict (approve, request changes, or reject)
- 🔍 Analyzes PR files for patterns and potential issues
- 🎯 Provides actionable feedback for PR authors

## Usage

### Basic Usage

```javascript
const { reviewPR } = require('./pr-reviewer-agent');

const result = await reviewPR({
  repo: 'owner/repo',
  prNumber: 123,
  token: 'your-github-token'
});

if (result.success) {
  console.log(result.markdown);
} else {
  console.error('Error:', result.error);
}
```

### Output Example

```markdown
# PR Review

## Summary

- **Title**: Add PR reviewer agent
- **Author**: claude-builder
- **Files Changed**: 2
- **Lines Added**: 205
- **Lines Removed**: 0

**Description**: Implement a PR reviewer agent that generates structured Markdown output

## Risks

No significant risks identified.

## Nitpicks

- **javascript** (pr-reviewer-agent.js): Consider adding JSDoc comments for better documentation

## Verdict

✅ **Approve** - This PR looks good and can be merged.
```

## Configuration

The agent accepts the following options:

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| repo | string | Yes | Repository owner/name (e.g., 'owner/repo') |
| prNumber | number | Yes | Pull request number |
| token | string | Yes | GitHub token for authentication |

## Error Handling

The agent will return an error if:
- The issue is not OPEN
- The issue has already been rewarded
- GitHub API authentication fails
- PR number doesn't exist

## Integration

This agent can be integrated into:
- GitHub Actions workflows
- CI/CD pipelines
- Manual review processes
- Automated review bots

## License

MIT License - see LICENSE file for details.
