# Claude Review Agent

`claude-review` analyzes a GitHub pull request diff and prints a structured Markdown review comment.

## Setup

```bash
chmod +x agents/claude-review/bin/claude-review
export PATH="$PWD/agents/claude-review/bin:$PATH"
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Offline mode for saved diffs:

```bash
claude-review --diff-file ./pull.diff --repo owner/repo --number 123
```

Write to a file:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Output Format

The agent prints:

- Summary of changes in 2-3 sentences
- Identified risks
- Improvement suggestions
- Confidence score: `Low`, `Medium`, or `High`

## Notes

- Uses only Python standard-library modules.
- Does not require `gh` or a GitHub token for public PRs.
- Falls back to GitHub's public `.diff` URL if the API is rate-limited.
- Uses a deterministic review heuristic so it works in CI and local shells.
- The bundled `CLAUDE.md` describes the agent contract if you want Claude Code to operate the same review workflow interactively.
