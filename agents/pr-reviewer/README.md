# claude-review — PR Review Sub-Agent

A Claude Code sub-agent that reviews GitHub pull requests and produces structured Markdown feedback with risk analysis and improvement suggestions.

## Features

- **CLI tool**: `claude-review --pr <url>` for on-demand reviews
- **GitHub Action**: automated review on every PR open/sync
- **Structured output**: summary, risks, suggestions, confidence score
- **Smart diff handling**: truncates large diffs with explicit notes
- **Zero npm dependencies**: pure bash + `gh` + `claude` CLI
- **Comment posting**: `--post` flag posts review directly to PR

## Quick Setup (2 commands)

```bash
# 1. Copy the agent to your PATH
cp agents/pr-reviewer/claude-review /usr/local/bin/
chmod +x /usr/local/bin/claude-review

# 2. Verify it works
claude-review --pr https://github.com/facebook/react/pull/36243
```

### Prerequisites

| Tool | Install |
|------|---------|
| [GitHub CLI](https://cli.github.com/) | `brew install gh` / `winget install GitHub.cli` |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | `npm install -g @anthropic-ai/claude-code` |

Both `gh` and `claude` must be authenticated:
```bash
gh auth login
claude auth login   # or set ANTHROPIC_API_KEY
```

## Usage

### CLI

```bash
# Basic review to stdout
claude-review --pr https://github.com/owner/repo/pull/123

# Save to file
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

# Post as PR comment
claude-review --pr https://github.com/owner/repo/pull/123 --post

# Use a specific model
claude-review --pr https://github.com/owner/repo/pull/123 --model claude-sonnet-4-20250514
```

### GitHub Action

Copy the workflow to your repo:

```bash
cp agents/pr-reviewer/.github/workflows/pr-review.yml .github/workflows/
```

Add `ANTHROPIC_API_KEY` to your repo secrets (Settings > Secrets > Actions).

The action triggers on `pull_request` events (opened, synchronize, reopened) and posts a structured review comment automatically.

## Output Format

```markdown
# PR Review: owner/repo#123

## Summary
This PR adds input validation to the user registration endpoint.
It introduces Zod schemas for email and password fields with proper
error messages. The implementation is clean and well-tested.

## Identified Risks
- Missing rate limiting on validation endpoint (src/routes/auth.ts:45)
- Zod schema allows empty strings for `name` field (src/schemas/user.ts:12)

## Improvement Suggestions
- Add `.min(1)` to the name field schema to prevent empty submissions
- Consider extracting shared validation patterns to a `lib/validators.ts`
- Add integration test for the full registration flow, not just unit tests

## Confidence Score
**High**
Small, focused PR with clear intent and well-structured diff.
```

## How It Works

1. **Fetches PR data** via GitHub API: metadata, file list, diff, existing comments
2. **Builds structured prompt** with all PR context and review instructions
3. **Sends to Claude** via `claude --print` for analysis
4. **Outputs structured Markdown** to stdout, file, or PR comment

The agent definition (`pr-review-agent.md`) provides Claude with:
- Review priorities (correctness > security > errors > performance > maintainability)
- Anti-patterns to flag (hardcoded secrets, `any` types, SQL injection, etc.)
- Confidence scoring criteria based on diff size and complexity
- Strict rules against hallucinating code not in the diff

## Test Results

Tested on 2 real GitHub PRs:

| PR | Repo | Lines Changed | Review |
|----|------|---------------|--------|
| [#36243](https://github.com/facebook/react/pull/36243) | facebook/react | +38/-3 | [test-outputs/react-36243.md](test-outputs/react-36243.md) |
| [#308831](https://github.com/microsoft/vscode/pull/308831) | microsoft/vscode | +5/-5 | [test-outputs/vscode-308831.md](test-outputs/vscode-308831.md) |

## License

MIT
