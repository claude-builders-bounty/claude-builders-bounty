# claude-review — PR Review Sub-Agent

A Claude Code sub-agent that reviews GitHub pull requests and produces structured Markdown reports.

## Features

- **CLI mode** — review any public GitHub PR via URL
- **Diff mode** — review a local `git diff` output file
- **GitHub Action** — auto-review every PR in your repo
- **6 review categories**:
  - Code style issues (line length, tabs, trailing whitespace, debug prints)
  - Potential bugs (None assignments, bare excepts, eval, empty blocks)
  - Security vulnerabilities (hardcoded secrets, SQL injection, XSS, command injection)
  - Performance concerns (O(n²) loops, sequential awaits, inefficient DOM queries)
  - Missing tests
  - Documentation gaps
- **Structured output** with severity (🔴 high / 🟡 medium / 🔵 low) and file:line references
- **Confidence score** (High / Medium / Low)
- **Optional auto-posting** as a PR comment via `GITHUB_TOKEN`

## Setup

```bash
pip install -r /dev/null  # no external dependencies — uses stdlib only
```

## CLI Usage

```bash
# Review a GitHub PR
python claude-review.py --pr https://github.com/owner/repo/pull/123

# Review a local diff
python claude-review.py --diff /tmp/pr_diff.txt

# Write output to file
python claude-review.py --pr https://github.com/owner/repo/pull/123 --output review.md

# Review and auto-post as PR comment
export GITHUB_TOKEN="ghp_..."
python claude-review.py --pr https://github.com/owner/repo/pull/123 --post-comment
```

## GitHub Action

Copy `.github/workflows/pr-review.yml` into your repository. On every PR open/sync, the action will:
1. Check out the code with full history
2. Generate a diff against the base branch
3. Run `claude-review.py` on the diff
4. Post the structured report as a PR comment

## Sample Output

See [SAMPLE_OUTPUT.md](./SAMPLE_OUTPUT.md) for example reviews on real GitHub PRs.

## As a Claude Code Sub-Agent

Include the `CLAUDE.md` file in your project root to register this tool as a Claude Code sub-agent. Then tell Claude:

> Claude, run the PR review agent on PR #123

## License

MIT
