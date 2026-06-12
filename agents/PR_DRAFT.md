# PR Draft: Complete Claude PR Review Agent

Closes #4.

## Summary

- Adds a dependency-free `claude-review` CLI that fetches a GitHub PR diff and renders a structured Markdown review.
- Adds a Claude Code sub-agent definition for the same structured review workflow.
- Adds a GitHub Actions workflow that generates and posts the same review on pull requests.
- Includes two reproducible sample outputs from real GitHub PRs and a verification script.

## Acceptance Criteria

- CLI: `agents/claude-review --pr https://github.com/owner/repo/pull/123`
- GitHub Action: `.github/workflows/pr-review.yml`
- Claude Code sub-agent: `.claude/agents/pr-reviewer.md`
- Structured Markdown output:
  - Summary of changes
  - Identified risks
  - Improvement suggestions
  - Confidence score: Low / Medium / High
- Tested on two real PRs:
  - `https://github.com/cli/cli/pull/1`
  - `https://github.com/fastapi/fastapi/pull/12592`
- README: `agents/README.md`

## Verification

```bash
python3 -m py_compile agents/claude-review && rm -rf agents/__pycache__
agents/scripts/verify-real-prs.sh
python3 agents/claude-review --pr https://github.com/cli/cli/pull/1 --output /tmp/claude-review-cli-1.md
```

Observed:

```text
Verified 2 real PR sample outputs.
```

## Local Submit Steps

```bash
git checkout bounty-4-pr-review-agent
git add .claude/agents/pr-reviewer.md .github/workflows/pr-review.yml agents/README.md agents/claude-review agents/samples/cli-1.md agents/samples/fastapi-12592.md agents/scripts/verify-real-prs.sh
git commit -m "Complete Claude PR review agent"
git push <your-fork> bounty-4-pr-review-agent
```

## Claim

After opening the PR, comment on issue #4:

```text
/opire try

Submitted PR: <PR URL>

This completes the Claude PR review agent bounty with CLI usage, GitHub Action support, structured Markdown output, two real PR sample outputs, and verification commands.
```
