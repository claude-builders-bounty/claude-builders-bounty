# Claude PR Reviewer

`claude-review` is a dependency-free CLI that turns a GitHub pull request diff
into a structured Markdown review comment.

It satisfies bounty #4 by accepting a PR URL, analyzing the diff, and returning:

- a 2-sentence summary of the change;
- identified risks;
- improvement suggestions;
- a Low / Medium / High confidence score.

## Install

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty
```

## Usage

```bash
python claude-review --pr https://github.com/owner/repo/pull/123
```

Shorthand PR references are also supported:

```bash
python claude-review --pr owner/repo#123
python claude-review --pr owner/repo/123
```

Save the generated Markdown:

```bash
python claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

Post or update an idempotent PR comment using the GitHub CLI:

```bash
python claude-review --pr https://github.com/owner/repo/pull/123 --post
```

`--post` uses a hidden `claude-review:bot` marker and updates the existing
reviewer comment on later runs instead of creating duplicates.

For offline testing, pass a saved diff:

```bash
python claude-review --diff-file ./sample.diff
```

The tool first fetches `https://github.com/owner/repo/pull/123.diff`. If that
fails and the GitHub CLI is installed, it falls back to `gh pr diff`.

## Test

```bash
python -m unittest
```

## GitHub Action

An optional workflow example is available at
`docs/claude-reviewer/github-action.yml`. Copy it into
`.github/workflows/claude-review.yml` in a repository that also contains this
reviewer, or adapt the checkout step to install the reviewer from your fork.
The workflow uses a hidden `claude-review:bot` marker and updates its previous
comment on subsequent pushes, so it does not spam a PR thread on every commit.
It requests `issues: write` because PR comments are issue comments in the
GitHub API.

## Samples

See the standalone generated outputs in `sample-outputs/`:

- `sample-outputs/archestra-5144.md`
- `sample-outputs/algora-299.md`

## Claude Code Agent

This repo also includes `.claude/agents/pr-reviewer.md`, so Claude Code users can
run the reviewer as a focused PR review agent backed by the CLI.
