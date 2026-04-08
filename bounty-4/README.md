# Bounty #4: Claude Code PR Review Sub-Agent

Automated PR review using Claude API with structured Markdown output.

## Quick Start

### CLI (Bash)

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
./claude-review.sh --pr https://github.com/owner/repo/pull/123
```

Post review as a comment:
```bash
./claude-review.sh --pr https://github.com/owner/repo/pull/123 --post
```

### CLI (Python)

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python reviewer.py --pr https://github.com/owner/repo/pull/123
```

### GitHub Action

The included `.github/workflows/auto-review.yml` automatically reviews PRs on open/sync.

1. Add `ANTHROPIC_API_KEY` to your repository secrets.
2. Copy `.github/workflows/auto-review.yml` to your repo.
3. Open a PR — review posts automatically.

## Requirements

- `gh` CLI authenticated (`gh auth login`)
- Python 3.10+ (for `reviewer.py`)
- `ANTHROPIC_API_KEY` environment variable
- `jq` (for `claude-review.sh`)

## Review Output Structure

Every review includes:

| Section       | Description                                    |
|---------------|------------------------------------------------|
| Summary       | 2-3 sentence overview of changes               |
| Risks         | List with severity (Critical/High/Medium/Low)  |
| Suggestions   | Numbered improvement suggestions               |
| Confidence    | Overall confidence: Low/Medium/High            |

## Sample Reviews

See `sample-reviews/` for example outputs from real PRs.

## Files

| File | Description |
|------|-------------|
| `claude-review.sh` | Bash CLI wrapper (~80 lines) |
| `reviewer.py` | Python reviewer (~200 lines) |
| `.github/workflows/auto-review.yml` | GitHub Action |
| `sample-reviews/` | Sample review outputs |
| `README.md` | This file |

## License

MIT
