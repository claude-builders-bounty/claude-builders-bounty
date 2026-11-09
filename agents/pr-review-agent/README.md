# PR Review Agent — Usage

## Install

1. Copy `pr-review-agent.js` to your project (e.g., `.claude/hooks/pr-review-agent.js`)
2. Set your GitHub token:

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

3. Run:

```bash
node pr-review-agent.js --pr-url https://github.com/owner/repo/pull/123
```

## Post to PR

```bash
node pr-review-agent.js --pr-url https://github.com/owner/repo/pull/123 --post-comment
```

## As Claude Code Skill

Add to your `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "node .claude/hooks/pr-review-agent.js --pr-url \"$TOOL_INPUT_COMMAND\" --post-comment"
      }
    ]
  }
}
```

## Test

```bash
node test-pr.js
```

Creates a temporary test repo, opens a PR with intentional issues, and verifies the agent detects them.
