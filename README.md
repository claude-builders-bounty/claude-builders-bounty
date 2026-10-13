# Claude Code / AI Sub-Agent PR Reviewer ($150 Bounty Solution)

Automated PR review agent that fetches any GitHub Pull Request diff, analyzes structural risks and code quality patterns, and outputs a structured Markdown review comment.

## Features & Acceptance Criteria Coverage
- **CLI Execution**: Run directly with `--pr https://github.com/owner/repo/pull/123`
- **GitHub Action Workflow**: Included at `.github/workflows/pr-review.yml` to automatically review incoming PRs and post structured comments
- **Structured Markdown Output**:
  1. Summary of changes (2–3 sentences)
  2. Identified risks (bulleted list)
  3. Improvement suggestions (bulleted list)
  4. Confidence score (`Low` / `Medium` / `High`)
- **Real PR Verification**: Tested on 2 live production GitHub PRs (`expressjs/express#5935` and `fastify/fastify#5712`) — full outputs included in [`SAMPLE_OUTPUTS.md`](./SAMPLE_OUTPUTS.md).

## Usage

### 1. CLI Usage
```bash
node pr-review-agent.js --pr https://github.com/expressjs/express/pull/5935
```

### 2. GitHub Action Usage
Include `.github/workflows/pr-review.yml` in your repository. On every `pull_request` event, the workflow runs `pr-review-agent.js` and posts the structured Markdown review directly to the PR conversation.
