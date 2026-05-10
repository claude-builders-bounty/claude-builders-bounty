# Claude Review Agent

`claude-review` is a dependency-free Claude Code review agent for bounty #4. It fetches a GitHub PR diff, analyzes changed files and risky patterns, and prints a structured Markdown comment that can be pasted into a PR discussion.

## Setup

1. Use Python 3.10 or newer.
2. From this repository, run `chmod +x claude-review`.
3. Optionally put it on your path with `ln -s "$PWD/claude-review" ~/.local/bin/claude-review`.

## Usage

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
./claude-review --diff-file ./sample.diff --output review.md
./claude-review --pr https://github.com/owner/repo/pull/123 --json
```

The Markdown output always includes:

- `Summary`
- `Identified Risks`
- `Improvement Suggestions`
- `Confidence`

## What It Checks

- Changed file mix: code, tests, docs, config, workflows, and database migrations.
- Missing tests for code changes.
- Dependency and lockfile changes.
- GitHub workflow permission/release risk.
- SQL migration risk.
- Added lines that resemble secrets.
- Destructive shell, SQL, or dynamic execution patterns.
- Large diffs that are hard to review in one pass.

## Claude Code Agent

The `.claude/agents/pr-reviewer.md` file defines how Claude Code should use this CLI as a PR-review sub-agent. The agent runs the command, reads the generated Markdown, and can post it only when public GitHub commenting is intended.

## Verification

Run the unit tests:

```bash
python3 -m unittest discover -s tests
```

Generate the included real-PR examples:

```bash
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/830 --output sample-outputs/pr-830-review.md
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/832 --output sample-outputs/pr-832-review.md
```
