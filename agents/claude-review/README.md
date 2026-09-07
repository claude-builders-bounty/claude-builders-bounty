# claude-review — structured PR review agent

## Setup

```bash
chmod +x agents/claude-review/claude-review
# optional symlink
ln -sf "$(pwd)/agents/claude-review/claude-review" /usr/local/bin/claude-review
```

Needs `gh` auth. For live reviews: Claude Code CLI (`claude`) **or** `ANTHROPIC_API_KEY`.

## Usage

```bash
claude-review --pr https://github.com/OWNER/REPO/pull/123
# or
claude-review --diff ./changes.diff
```

## Output

Markdown with **Summary**, **Risks**, **Suggestions**, and **Confidence** (Low/Medium/High). Samples land in `samples/reviews/`.

## GitHub Action

See `agents/claude-review/action.yml` + `.github/workflows/claude-review.yml`.
