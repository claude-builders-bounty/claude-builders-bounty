# PR Reviewer Agent

Claude Code pull request reviewer that fetches a PR diff and returns a structured Markdown review.

## Install

```bash
chmod +x agents/pr-reviewer/claude_review.py && ln -sf "$PWD/agents/pr-reviewer/claude_review.py" /usr/local/bin/claude-review
```

If `/usr/local/bin` is not writable, run the script directly:

```bash
python3 agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

By default the command tries to call `claude -p` with the bundled agent prompt. If the Claude Code CLI is not installed, it falls back to a deterministic local reviewer so CI and first-time users still get structured output.

Useful flags:

- `--offline`: skip Claude and use the local reviewer
- `--output review.md`: write the Markdown review to a file
- `--token-env GITHUB_TOKEN`: use a GitHub token from the named environment variable

## Output Shape

Each review includes:

- Summary of changes in 2 to 3 sentences
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High

## GitHub Action

Copy `.github/workflows/claude-pr-review.yml` into a repository and set a `CLAUDE_API_KEY` or install Claude Code on the runner. The action runs on pull requests and uploads the review as an artifact.

## Sample Outputs

See `samples/real-pr-1.md` and `samples/real-pr-2.md` for outputs generated against real public GitHub pull requests.

