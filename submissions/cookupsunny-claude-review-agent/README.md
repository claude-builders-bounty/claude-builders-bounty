# Claude PR Review Agent

This submission implements bounty `#4`: a Claude Code PR-review agent that accepts a GitHub pull request URL and returns a structured Markdown review comment.

## Features

- CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- Claude Code integration through a dedicated `pr-reviewer` sub-agent
- Deterministic fallback analyzer for local testing and CI without private API keys
- Optional `--post-comment` mode using `GITHUB_TOKEN`
- GitHub Actions workflow example
- Unit tests and two real PR sample outputs
- `curl` fallback for Python installs with missing local TLS certificates

## Setup

From this directory:

```bash
chmod +x claude-review
python3 -m unittest discover -s tests
```

Claude Code is optional for verification. When the `claude` CLI is available, the tool uses:

```bash
claude --bare --print --agents '{"pr-reviewer": ...}' --agent pr-reviewer
```

Without Claude Code, the CLI still returns the required sections using the built-in analyzer.

## Usage

Review a public PR:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

Run the deterministic analyzer only:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --no-claude
```

Review an already downloaded diff:

```bash
./claude-review \
  --pr https://github.com/owner/repo/pull/123 \
  --diff-file /tmp/pr.diff \
  --no-claude
```

Post the structured review comment back to the PR:

```bash
GITHUB_TOKEN=ghp_xxx ./claude-review \
  --pr https://github.com/owner/repo/pull/123 \
  --post-comment
```

The output format always contains:

- `## Summary`
- `## Identified Risks`
- `## Improvement Suggestions`
- `## Confidence Score`

## GitHub Action

An example workflow is included at `github-action/claude-review.yml`. Copy it into `.github/workflows/claude-review.yml` in a target repository. It runs on PR updates and posts the generated review as a PR comment.

Required repository secret:

- `ANTHROPIC_API_KEY` if the workflow should use Claude Code instead of the fallback analyzer

GitHub provides `GITHUB_TOKEN` automatically.

## Verification

```bash
python3 -m unittest discover -s tests
python3 -m py_compile claude_review.py claude-review tests/test_claude_review.py
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/926 --no-claude
```

Sample outputs generated from real GitHub PRs are in `examples/`.
