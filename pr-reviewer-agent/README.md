# Claude PR Reviewer Agent

`claude-review` is a self-contained Claude Code PR reviewer agent. It accepts a public GitHub pull request URL, reads the PR diff, and prints a structured Markdown review comment with a short summary, risks, suggestions, and a confidence score.

The command works without GitHub credentials for public PRs and has no third-party Python dependencies. When the Claude Code CLI is available, `--use-claude` can route the diff through Claude; otherwise the built-in deterministic reviewer still produces the required structured output.

## Install

From this folder:

```bash
chmod +x bin/claude-review
```

Optionally add the `bin` directory to your `PATH`:

```bash
export PATH="$PWD/bin:$PATH"
```

## Usage

Review a public GitHub PR:

```bash
bin/claude-review --pr https://github.com/owner/repo/pull/123
```

Write the Markdown review to a file:

```bash
bin/claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

Review a local diff:

```bash
bin/claude-review --diff-file ./example.diff
```

Use the Claude Code CLI when it is installed and authenticated locally:

```bash
bin/claude-review --use-claude --pr https://github.com/owner/repo/pull/123
```

The deterministic fallback is useful for CI and for reviewers who do not want to connect any account. The Claude path is optional because this bounty deliverable must be runnable from a clean checkout.

## Output Format

Every run emits Markdown with:

- `### Summary of Changes`
- `### Identified Risks`
- `### Improvement Suggestions`
- `### Confidence Score: Low|Medium|High`

## Claude Code Sub-Agent Prompt

The reusable sub-agent prompt lives at `claude-agents/pr-reviewer.md`. You can copy it into a Claude Code agent setup or use the CLI's `--use-claude` flag to send an equivalent prompt to the local `claude` binary.

## Optional GitHub Action

This folder includes `github-action/claude-review.yml` as a copy-paste workflow example. It posts the generated review as a PR comment using the default `GITHUB_TOKEN`. The CLI route above is the primary acceptance path.

## Sample Outputs

Two real public PR runs are included in:

- `samples/github-gitignore-4857.md`
- `samples/github-gitignore-4500.md`

Regenerate them with:

```bash
bin/claude-review --pr https://github.com/github/gitignore/pull/4857 --output samples/github-gitignore-4857.md
bin/claude-review --pr https://github.com/github/gitignore/pull/4500 --output samples/github-gitignore-4500.md
```

## Verify

```bash
PYTHONPATH=src python3 -m unittest discover tests
```
