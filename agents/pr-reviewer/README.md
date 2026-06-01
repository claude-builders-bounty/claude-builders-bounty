# Claude PR Review Agent

`claude-review` reads a GitHub pull request diff and prints a structured Markdown review comment.

## Install

```bash
chmod +x bin/claude-review
export PATH="$PWD/bin:$PATH"
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

For offline review or CI artifacts:

```bash
claude-review --diff-file ./change.diff --repo owner/repo#123
```

## Output

The comment includes:

- Summary of changes.
- Identified risks.
- Improvement suggestions.
- Changed surface.
- Confidence score: `Low`, `Medium`, or `High`.

Two example reviews generated from public GitHub PRs are included in `examples/`.

## Notes

The agent uses Python standard library only and fetches `https://github.com/owner/repo/pull/123.diff`.
It does not require GitHub credentials for public PRs.
