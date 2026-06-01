# Claude Review Agent

CLI agent that reviews a GitHub pull request diff and returns a structured Markdown review comment.

This package also includes a Claude Code sub-agent definition at
`.claude/agents/pr-reviewer.md` so the workflow can be invoked as a reusable
agent in repositories that load local Claude agents.

## Setup

No third-party dependencies are required.

```bash
python pr_reviewer/claude_review.py --help
```

Optionally place the repository root on your `PATH` so the `claude-review` shim is available.

## Usage

Review a public GitHub pull request:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

On Windows from the repository root:

```cmd
.\claude-review.cmd --pr https://github.com/owner/repo/pull/123
```

Review a local diff file:

```bash
python pr_reviewer/claude_review.py --diff-file samples/octocat-hello-world-6.diff
```

Write the Markdown review to a file:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

Post the review as a PR comment:

```bash
GITHUB_TOKEN=ghp_... claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

The included GitHub Action at `.github/workflows/claude-pr-review.yml` runs the
same command on pull requests and posts the structured Markdown comment with the
repository `GITHUB_TOKEN`.

## Output Format

The generated Markdown contains:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High
- Optional GitHub PR comment URL when `--post-comment` is used

## Verification

```bash
python -m py_compile pr_reviewer/claude_review.py pr_reviewer/test_claude_review.py
python pr_reviewer/test_claude_review.py
```

Sample outputs are included under `samples/`.

## Claude Code Sub-Agent

Copy or keep `.claude/agents/pr-reviewer.md` in a repository to expose a
`pr-reviewer` sub-agent. The sub-agent delegates the repeatable diff parsing and
Markdown rendering to `pr_reviewer/claude_review.py`, then returns a comment
with the required summary, risks, suggestions, and confidence sections.
