# PR Reviewer agent (`claude-review`)

Bounty: [#4 — AGENT: PR reviewer with structured Markdown output](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

`claude-review` takes a GitHub PR URL, sends the diff to Claude, and returns a
structured Markdown review: **Summary / Risks / Suggestions / Confidence**.

## Setup (2 commands)

```bash
# 1. have gh and claude installed and authenticated
gh auth status && claude --version

# 2. make the script available on PATH
chmod +x claude-review && sudo cp claude-review /usr/local/bin/
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
claude-review --pr <url> --model claude-sonnet-4-20250514 --out review.md
```

Options:

| flag | purpose |
|---|---|
| `--pr` (required) | GitHub PR URL to review |
| `--model` | override model (default: your `claude` CLI default) |
| `--out` | write the review to a file instead of stdout |

## GitHub Action variant

`github-action.yml` runs the same review on every `pull_request` event and posts
the result as a PR comment. Copy it to `.github/workflows/claude-review.yml` in
the target repo and add your key as the `ANTHROPIC_API_KEY` repository secret.

## Sample outputs (real PRs)

- [samples/sample-output-1.md](samples/sample-output-1.md) — calcom/cal.com#30365 (TypeScript, 34 s)
- [samples/sample-output-2.md](samples/sample-output-2.md) — pydantic/pydantic#14003 (Python/Rust, 40 s)

Both runs used the CLI path end to end (fetch diff → review → structured output)
with no manual editing of the review text.

## Notes

- The script is read-only: it fetches the diff and posts nothing by itself.
- Works from any current directory (uses `--repo`, never the local git tree).
- Exits non-zero on: unparseable URL, empty diff, missing `gh`/`claude` binary.
