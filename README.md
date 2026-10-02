# claude-review

A Claude Code sub-agent that reviews PRs and posts structured Markdown comments.

## Install

```bash
pip install -e .
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

## Configuration

Set one of these environment variables for the LLM backend:

| Variable | Backend | Default |
|----------|---------|---------|
| OLLAMA_HOST | Local Ollama | http://127.0.0.1:11434 |
| ANTHROPIC_API_KEY | Anthropic Claude | - |
| OPENROUTER_API_KEY | OpenRouter | - |

## GitHub Action

Copy `.github/workflows/claude-review.yml` into your repo to auto-review on PR open.

## Output

Structured Markdown with:
- Summary (2-3 sentences)
- Risks (list)
- Suggestions (list)
- Confidence score (Low/Medium/High)
