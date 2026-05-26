# claude-review — Claude Code PR Review Agent

> Claude Code sub-agent that reviews GitHub pull requests and returns structured, actionable feedback.

## Quick Start

```bash
# Install
curl -o /usr/local/bin/claude-review https://raw.githubusercontent.com/ybbuge2537/claude-builders-bounty/feat/claude-review-agent/claude-review
chmod +x /usr/local/bin/claude-review
pip install --upgrade claude-code

# Review a PR
export GITHUB_TOKEN="ghp_xxx"
claude-review --pr https://github.com/owner/repo/pull/123
```

## Usage

### CLI Mode

```bash
claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2118
```

### Claude Code Slash Command

Add `.claude/commands/review.md` to your project, then:

```
/review https://github.com/owner/repo/pull/123
```

### GitHub Action

Copy `.github/workflows/claude-review.yml` to your repo. Set `ANTHROPIC_API_KEY` in repository secrets. The action triggers on new PRs and on `/review` comments.

## Output Format

Every review follows this structure:

```markdown
## PR Review: {title}

### Summary
{One paragraph}

### Issues Found
- 🔴 Critical — must fix before merge
- 🟡 Warning — should fix
- 🔵 Note — consider fixing

### Suggestions
{Non-blocking improvements}

### Security
{Security assessment}

### Confidence
**Overall confidence: [Low/Medium/High]**
{Explanation}
```

## Sample Outputs

See [SAMPLE_OUTPUTS.md](./SAMPLE_OUTPUTS.md) for real reviews generated on actual PRs.

## Requirements

- Python 3.8+
- Claude Code CLI (`claude`)
- GitHub token with `repo` scope
