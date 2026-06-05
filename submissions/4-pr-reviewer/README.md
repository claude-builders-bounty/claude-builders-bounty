# Claude Code PR Reviewer Agent

Automated pull request review agent that fetches a PR diff and produces
a structured Markdown review comment via Claude Code.

## Install

```bash
cp claude-review ~/.claude/agents/pr-reviewer
chmod +x ~/.claude/agents/pr-reviewer
```

## Usage

```bash
# Direct
python3 claude-review --pr https://github.com/owner/repo/pull/123

# Via Claude Code agent
claude --agent pr-reviewer --pr https://github.com/owner/repo/pull/123
```

Set `GITHUB_TOKEN` for authenticated API access (avoids rate limits).

## Output Structure

| Section | Content |
|---------|---------|
| Summary | 2–3 sentence overview |
| Risks | Specific concerns with reasoning |
| Suggestions | Actionable improvements |
| Confidence | Low / Medium / High with explanation |
