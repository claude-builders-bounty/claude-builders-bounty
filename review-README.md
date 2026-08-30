# claude-review — PR review sub-agent

A Claude Code sub-agent that takes a pull request, reviews it via the Claude
API, and outputs a structured Markdown review — optionally posting it as a
comment on the PR.

## Usage

### Option A — CLI

```bash
export ANTHROPIC_API_KEY=sk-ant-...
pip install --no-cache-dir urllib3 2>/dev/null || true
python3 claude-review.py --pr https://github.com/owner/repo/pull/123
# write to file:
python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --out review.md
# post as a PR comment:
python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --post --token ghp_...
```

### Option B — GitHub Action

Add to `.github/workflows/claude-review.yml` (the included `review-workflow.yml`)
and set a repository secret `ANTHROPIC_API_KEY`. Every new/synced PR gets an
automatic structured review comment.

## Output

Every review is strict Markdown with these sections:

| Section | Content |
|---|---|
| **Summary** | 2–3 sentence overview of changes |
| **Risks** | bulleted list of security/correctness concerns |
| **Suggestions** | concrete improvement ideas |
| **Confidence** | `High` / `Medium` / `Low` |

## Tested on real PRs

- **PR claude-builders-bounty/claude-builders-bounty#3960** (GPT Weekly Dev Summary n8n workflow) → `High` confidence: clean, self-contained, meets criteria.
- **PR claude-builders-bounty/claude-builders-bounty#3961** (pre-tool-use bash blocker hook) → `Medium` confidence: solid security hook; minor suggestion to expand `rm -rf` regex edge cases.

Sample outputs from both are reproducible by running the CLI with `--pr` against
those URLs.

## Requirements

- Python 3.9+
- `ANTHROPIC_API_KEY` (Claude API key) for review generation
- `--token ghp_...` only when using `--post`
