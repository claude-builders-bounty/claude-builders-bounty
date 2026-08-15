# Claude Review Agent

Lightweight zero-dependency Claude Code sub-agent that reviews a GitHub PR from its diff and posts a structured Markdown review comment.

## Features
- Fetches the diff of any public GitHub PR via `.diff` URL
- Zero external Python dependencies (stdlib `urllib` only)
- Sends the diff to Claude's Messages API (`claude-3-5-sonnet-20241022`)
- Outputs structured review with 4 sections:
  - **Summary of Changes** — 2–3 sentence overview
  - **Identified Risks** — bugs, security issues, edge cases
  - **Improvement Suggestions** — actionable recommendations
  - **Confidence Score** — Low / Medium / High

## Usage (CLI)

```bash
# 1. Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...

# 2. Review any public PR
python claude-review.py --pr https://github.com/owner/repo/pull/123
```

The review is printed to stdout, formatted as Markdown.

## Usage (GitHub Action)

1. Add `.github/workflows/claude-review.yml` (see `claude-review-workflow.yml` in this repo)
2. Add your API key as a repository secret named `ANTHROPIC_API_KEY`
3. The workflow runs on every PR open / update / ready-for-review and posts a review comment automatically

## Example Output

See `samples/test-output.txt` for real outputs from two tested PRs:

1. `vercel/next.js#8431` — small env-flag change
2. `nodejs/node#50000` — GH Actions upload-artifact pin bump

Full sample:

```
### Summary of Changes
Add `ADBLOCK` and `DISABLE_OPENCOLLECTIVE` to child process env when installing dependencies.

### Identified Risks
- Child process inherits all env vars; added vars may affect other tools if reused.
- No validation of `command` or `args`; potential crash if undefined.

### Improvement Suggestions
- Keep env spread immutable: `env: { ...process.env, ADBLOCK: '1', DISABLE_OPENCOLLECTIVE: '1' }`.
- Add guard: `if (!command) reject({ command: 'missing command' })`.

### Confidence Score
Medium – diff small, logic straightforward, but edge cases exist.
```

## Cost / Limits
- Diff larger than 100KB is truncated to the first 100KB (note printed to stderr)
- One API call per review run

## License
MIT