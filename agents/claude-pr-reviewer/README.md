# Claude PR Reviewer

`claude-review` is a Claude Code-oriented PR review agent that accepts a GitHub
pull request URL, reads the PR diff with the GitHub CLI, and prints a structured
Markdown review.

The output always contains:

- `Summary`
- `Identified Risks`
- `Improvement Suggestions`
- `Confidence`

When the `claude` CLI is installed, the agent sends the PR metadata and diff to
Claude Code with a strict review prompt. When Claude Code is not installed, the
agent falls back to a deterministic local review based on changed paths and diff
markers so the command still works in CI or a fresh machine.

By default the command only prints Markdown. Add `--post-comment` when you want
the validated Markdown posted to the PR through `gh pr comment`.

## Install

```bash
install -m 755 agents/claude-pr-reviewer/bin/claude-review /usr/local/bin/claude-review
```

## Use

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

For deterministic sample generation without calling Claude Code:

```bash
claude-review --no-claude --pr https://github.com/owner/repo/pull/123
```

To post the generated review as a GitHub PR comment after validation:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

## Requirements

- Python 3.10 or newer
- GitHub CLI authenticated for public PR reads: `gh auth status`
- Optional: Claude Code CLI available as `claude`

## Behavior

1. Parses the GitHub PR URL.
2. Runs `gh pr view` for title, author, branch, additions, deletions, and changed
   file count.
3. Runs `gh pr diff` to collect the patch.
4. Builds a Claude prompt that requires the exact Markdown sections.
5. Uses Claude Code when available, otherwise generates a deterministic local
   review.
6. Verifies the required Markdown headings before printing.
7. Posts the validated review only when `--post-comment` is provided.

## Notes

- The command prints to stdout so it can be redirected, archived, or posted.
- The command does not post comments by default. That keeps review generation
  separate from externally visible GitHub actions unless `--post-comment` is
  explicit.
- Large PRs may produce lower confidence because the diff can exceed the context
  that is reasonable for a single review pass.
