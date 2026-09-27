# Claude PR Reviewer — $150 Bounty #4

Claude Code sub-agent that fetches any GitHub PR diff and returns a **structured Markdown review** via `claude-sonnet-4-20250514`.

Output is always:
- **Summary** (2–3 sentences)
- **Risks** (list)
- **Suggestions** (list)
- **Confidence** — Low / Medium / High

## Setup (5 steps)

1. **Clone & install**
   ```bash
   git clone <this-repo> && cd bounties/claude-builders-4
   npm install -g .
   # or local: npm link
   ```

2. **Set credentials**
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...   # required for Claude review
   export GITHUB_TOKEN=ghp_...           # optional — higher rate limit + --comment
   ```
   Without `ANTHROPIC_API_KEY` the CLI falls back to a heuristic review so the pipeline never blocks.

3. **Run the CLI**
   ```bash
   claude-review --pr https://github.com/owner/repo/pull/123
   # save to file
   claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
   # post as PR comment (needs GITHUB_TOKEN)
   claude-review --pr https://github.com/owner/repo/pull/123 --comment
   ```

4. **(Optional) Install the GitHub Action** — copy `.github/workflows/claude-review.yml` to your repo, add `ANTHROPIC_API_KEY` to **Settings → Secrets**, and the review runs automatically on every `pull_request` event. You can also use it as a reusable action via `action.yml`:
   ```yaml
   - uses: ./bounties/claude-builders-4
     with:
       pr_url: ${{ github.event.pull_request.html_url }}
       anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
   ```

5. **Verify** — check `examples/` for two real PR reviews produced by this tool:
   - [`examples/PR-4491-review.md`](examples/PR-4491-review.md) — PR #4491 (Ialyahya96, 4 files +182)
   - [`examples/PR-4490-review.md`](examples/PR-4490-review.md) — PR #4490 (QIU-Guanzong, 21 files +1585)
   ```bash
   claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4491
   claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4490
   ```

## CLI reference

```
claude-review --pr <url> [options]
  --pr <url>        PR URL (required) — also accepts bare https://github.com/.../pull/N
  --output <file>   Write Markdown to file (default: stdout)
  --comment         Post review as PR comment (requires GITHUB_TOKEN)
  --json            Also emit JSON alongside Markdown
  --help, -h        Help
```

## How it works

1. Parses `owner/repo/pull/number` from the URL.
2. Fetches PR metadata + diff + file list via `api.github.com` (with `application/vnd.github.v3.diff`).
3. Truncates per-file patches (>20k) and total diff (>120k) to stay within context.
4. Calls `claude-sonnet-4-20250514` (`POST /v1/messages`, `max_tokens: 2048`) with a strict-JSON system prompt, then formats to Markdown.
5. Optionally posts the Markdown as an issue comment via `POST /repos/{owner}/{repo}/issues/{number}/comments`.

## Requirements

- Node.js ≥ 18 (global `fetch`)
- `ANTHROPIC_API_KEY` for Claude-powered reviews; `GITHUB_TOKEN` for private repos / commenting / higher rate limits
