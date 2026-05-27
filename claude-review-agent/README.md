# 🤖 Claude Review — AI-Powered PR Review Agent

Drop this script into any repo. Give it a PR URL, get a structured code review back.

## Quick Start

```bash
# 1. Set your API key
export DEEPSEEK_API_KEY="sk-..."    # or ANTHROPIC_API_KEY

# 2. (Optional) Set GitHub token for higher rate limits
export GITHUB_TOKEN="ghp_..."

# 3. Run it
python3 claude-review --pr https://github.com/owner/repo/pull/123
```

## Usage

```
claude-review --pr <URL> [--model deepseek-chat] [--json]
```

| Flag | Description |
|------|-------------|
| `--pr` | GitHub PR URL (required) |
| `--model` | AI model (default: `deepseek-chat`, also supports `claude-sonnet-4-20250514`) |
| `--json` | Output raw JSON instead of Markdown |

## Output

A structured Markdown review with:

- **Summary** — 2-3 sentence overview
- **Risks** — severity-rated issues (🔴 high / 🟡 medium / 🟢 low)
- **Suggestions** — categorized improvement ideas (bug, performance, security, style, architecture, testing)
- **Confidence** — 🔴 low / 🟡 medium / 🟢 high

## How It Works

1. Parses the PR URL → extracts owner/repo/number
2. Fetches PR diff via GitHub API (with token if available)
3. Sends diff to AI with a structured review prompt
4. Parses JSON response → renders Markdown

## Sample Output

See `sample_review_1.md` and `sample_review_2.md` for real outputs.

## Configuration

| Env Var | Required | Default |
|---------|----------|---------|
| `DEEPSEEK_API_KEY` | Yes* | — |
| `ANTHROPIC_API_KEY` | Yes* | — |
| `GITHUB_TOKEN` | No | — |
| `AI_BASE_URL` | No | `https://api.deepseek.com/v1` |
| `CLAUDE_REVIEW_MODEL` | No | `deepseek-chat` |

*At least one AI API key required.

If `ANTHROPIC_API_KEY` is set and `DEEPSEEK_API_KEY` is not set, the script uses Anthropic's native Messages API. Otherwise it uses the OpenAI-compatible `/chat/completions` endpoint configured by `AI_BASE_URL`.

## Dependencies

Only one external Python dependency: `requests`.

```bash
pip install requests
```

## Validation

```bash
python3 -m py_compile claude-review
python3 claude-review --help
```

---

*Part of the [Claude Builders Bounty](https://github.com/claude-builders-bounty) program · Issue #4*
