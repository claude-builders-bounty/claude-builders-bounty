# Claude PR Reviewer Agent

`claude-review` is a small Claude Code-oriented PR review agent. It takes a GitHub pull request URL or a local diff file, inspects the patch, and emits a structured Markdown review comment that can be pasted into GitHub or posted directly with `--post`.

## Install

No package install is required. The agent uses only the Python standard library.

```bash
python agents/pr-reviewer/claude_review.py --help
```

Optional shell alias:

```bash
alias claude-review="python agents/pr-reviewer/claude_review.py"
```

## Usage

Review a public GitHub PR and print Markdown:

```bash
python agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123
```

Review a saved diff:

```bash
python agents/pr-reviewer/claude_review.py --diff-file ./sample.diff --pr https://github.com/owner/repo/pull/123
```

Write output to a file:

```bash
python agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

Post the structured Markdown as a PR conversation comment:

```bash
GITHUB_TOKEN=ghp_xxx python agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123 --post
```

`--post` writes to the GitHub issue comments API for the PR. It requires a token with permission to comment on that repository.

## Output Contract

The generated comment always contains:

- Summary of changes in 2 sentences.
- Identified risks as a list.
- Improvement suggestions as a list.
- Confidence score: `Low`, `Medium`, or `High`.

## How It Reviews

The agent intentionally uses deterministic patch analysis instead of calling an external LLM API:

- summarizes file types and changed areas from `diff --git` headers
- counts additions and deletions
- identifies risk signals such as auth, secrets, migrations, workflows, hooks, generated assets, and missing tests
- produces practical suggestions based on touched files and observed risk

This makes the agent easy to run in CI, predictable for maintainers, and safe to use on public pull requests without sending code to another service.

## Samples

Two real PR sample outputs are included:

- `samples/owk-004-badge-system-pr-17.md`
- `samples/bounty-hunter-currency-pr-141.md`

## Validation

```bash
python agents/pr-reviewer/tests/test_claude_review.py
python agents/pr-reviewer/claude_review.py --diff-file agents/pr-reviewer/tests/fixtures/simple.diff --pr https://github.com/example/repo/pull/1
```
