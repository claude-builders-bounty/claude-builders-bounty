# Claude PR Reviewer

`claude-review` is a Claude Code-friendly PR review agent that reads a GitHub
pull request diff and returns a structured Markdown review comment.

## Install

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -e agents/pr-reviewer
```

For a no-install run from the repository root:

```bash
python3 agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123
```

## Usage

Review a public GitHub PR:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Review a local diff:

```bash
claude-review --diff ./changes.diff
```

Write the Markdown comment to a file:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

Post the generated review directly to the pull request:

```bash
GITHUB_TOKEN=ghp_xxx claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

The token needs permission to write issue comments on the target repository.
For GitHub Actions, the default `secrets.GITHUB_TOKEN` works when the workflow
sets `issues: write`.

## GitHub Action

An example workflow that generates and posts the structured review comment is
included in:

```text
agents/pr-reviewer/examples/github-action.yml
```

Copy it to `.github/workflows/claude-pr-review.yml` in a repository that also
contains this package, or adapt the install step to point at your packaged copy.

## Output Format

The generated comment always includes:

- `Summary of Changes`
- `Identified Risks`
- `Improvement Suggestions`
- `Confidence Score`
- a collapsible list of changed files analyzed

The confidence score is `Low`, `Medium`, or `High`, based on diff size, test
presence, and risk signals such as dependency, CI, configuration, and
security-sensitive changes.

## Claude Code Agent

The companion agent prompt is in:

```text
.claude/agents/pr-reviewer.md
```

It tells Claude Code how to invoke the CLI, interpret the diff, and return the
structured Markdown review comment.

## Verification

```bash
python3 -m unittest discover -s agents/pr-reviewer/tests
```

Sample outputs from two real GitHub PRs are included in:

```text
agents/pr-reviewer/samples/
```
