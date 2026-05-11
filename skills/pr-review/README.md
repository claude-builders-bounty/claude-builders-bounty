# claude-review

A Claude-powered GitHub PR reviewer that produces structured Markdown analysis.

## Setup

**Step 1** — Install:
```bash
pip install -e path/to/skills/pr-review/
```

**Step 2** — Set your API key:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

**Step 3** — Review a PR:
```bash
claude-review --pr https://github.com/owner/repo/pull/42
```

---

## Output format

Every review produces four sections:

```
## Summary
(2–3 sentences)

## Identified Risks
- ...

## Improvement Suggestions
- ...

## Confidence Score
Low | Medium | High
```

See [`examples/`](examples/) for real outputs against public PRs.

---

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--pr URL` | required | GitHub PR URL |
| `--model MODEL` | `claude-haiku-4-5-20251001` | Claude model ID |
| `--output FILE` | stdout | Write review to a file |

Set `GITHUB_TOKEN` to raise the GitHub API rate limit from 60 to 5000 req/h.

---

## GitHub Actions

Copy [`github-action/pr-review.yml`](github-action/pr-review.yml) to `.github/workflows/pr-review.yml` in your repo and add `ANTHROPIC_API_KEY` as a repository secret. Every opened or updated PR will receive an automatic review comment.

---

## Claude Code skill

Copy [`SKILL.md`](SKILL.md) to `~/.claude/skills/review-pr.md` and invoke it inside Claude Code:

```
/review-pr https://github.com/owner/repo/pull/42
```

No separate API key required — Claude Code's own session handles the inference.
