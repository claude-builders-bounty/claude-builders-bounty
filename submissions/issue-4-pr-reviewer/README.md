# Claude Code PR Reviewer — Issue #4

A zero-dependency Python CLI + GitHub Action that reviews any GitHub PR using Claude API and produces a structured Markdown report.

## Setup (3 steps)

```bash
# 1. Set your API keys
export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_TOKEN=ghp_...    # for private repos and --post-comment

# 2. Run directly
python3 claude-review.py --pr https://github.com/owner/repo/pull/123

# 3. Or install globally
cp claude-review.py /usr/local/bin/claude-review && chmod +x /usr/local/bin/claude-review
claude-review --pr owner/repo/123
```

## Usage

```bash
# Review a PR from URL
python3 claude-review.py --pr https://github.com/owner/repo/pull/123

# Short form
python3 claude-review.py --pr owner/repo/123

# Post review as GitHub comment
python3 claude-review.py --pr owner/repo/123 --post-comment

# JSON output (for automation)
python3 claude-review.py --pr owner/repo/123 --json > review.json

# Use a different model
python3 claude-review.py --pr owner/repo/123 --model claude-opus-4-5
```

## Output Format

Every review contains:

- **Summary** — 2–3 sentences describing what the PR does
- **Identified Risks** — security, correctness, performance, maintainability
- **Improvement Suggestions** — numbered, actionable, file-specific
- **Confidence Score** — Low / Medium / High with rationale

See [sample-output-1.md](sample-output-1.md) and [sample-output-2.md](sample-output-2.md) for real examples.

## GitHub Action

Copy [`.github/workflows/claude-review.yml`](.github/workflows/claude-review.yml) to your repo.

Add two repository secrets:
- `ANTHROPIC_API_KEY` — your Anthropic API key
- `GITHUB_TOKEN` — automatically provided by GitHub Actions

Reviews are posted automatically as comments on every new/updated PR.

## Claude Code Skill

Copy [`SKILL.md`](SKILL.md) to `~/.claude/commands/review-pr.md` to use as a Claude Code skill:

```bash
cp SKILL.md ~/.claude/commands/review-pr.md
# Then in Claude Code:
# /review-pr https://github.com/owner/repo/pull/123
```

## Design choices

- **Zero dependencies** — pure Python stdlib (`urllib.request`, `json`, `re`)
- **Works on public repos** without any token
- **Private repos** need `GITHUB_TOKEN` with `repo` scope
- **Large PRs** (>80 KB) are automatically truncated with a notice
- **Multi-model** — switch with `--model` flag
- **JSON mode** — pipe output to other tools
