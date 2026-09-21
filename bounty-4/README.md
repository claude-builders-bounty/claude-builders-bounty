# Claude PR reviewer — bounty #4

`claude-review` is a zero-Python-dependency CLI that accepts a public GitHub
pull-request URL, fetches its metadata and diff, asks the authenticated Claude
Code CLI for a focused review, validates the required structure, and prints the
review as Markdown.

It also includes a Claude Code sub-agent definition at
`.claude/agents/pr-reviewer.md`.

## Setup

Requirements:

- Python 3.10+
- Claude Code installed and authenticated (`claude` on `PATH`)
- Optional `GITHUB_TOKEN` for higher GitHub API limits
- `GITHUB_TOKEN` is required only when using `--post`

Make the CLI executable:

```bash
chmod +x bounty-4/claude-review
```

No `pip install` step is required.

## Usage

Review a pull request:

```bash
./bounty-4/claude-review \
  --pr https://github.com/owner/repo/pull/123
```

Save the review while also printing it:

```bash
./bounty-4/claude-review \
  --pr https://github.com/owner/repo/pull/123 \
  --output review.md
```

Post the validated Markdown back to the pull request:

```bash
export GITHUB_TOKEN=github_token_with_comment_permission

./bounty-4/claude-review \
  --pr https://github.com/owner/repo/pull/123 \
  --post
```

The output contract is deliberately narrow:

```markdown
## Summary
Two or three sentences.

## Risks
- Concrete risk.

## Improvement suggestions
- Concrete action.

## Confidence
High
```

If Claude omits a required section, returns sections out of order, omits the
risk/improvement lists, or uses a confidence value other than
`Low`/`Medium`/`High`, the CLI exits non-zero instead of posting malformed
output.

## Configuration

- `GITHUB_TOKEN` — optional for public reads; required for `--post`.
- `CLAUDE_REVIEW_COMMAND` — command used to invoke Claude Code. Defaults to
  `claude`; useful when the executable lives at a nonstandard path.
- `CLAUDE_REVIEW_MODEL` — optional model passed through as `--model`.
- `--max-diff-chars` — review budget for very large diffs; defaults to 120,000
  characters.

When a diff exceeds the configured budget it is truncated, and the prompt
explicitly requires the reviewer to disclose that limitation and lower
confidence when the omitted context may matter.

## Security boundary

PR titles, metadata, filenames, and diff contents are treated as untrusted.
The prompt explicitly forbids following instructions embedded in the diff.
Shell execution is avoided for both GitHub access and Claude invocation.

`--post` is opt-in. A normal review only prints Markdown; it never mutates the
target repository.

## Real-PR sample outputs

The required sample reviews are committed under `samples/` and are tied to
real public pull requests and exact heads:

1. `claude-builders-bounty/claude-builders-bounty#4370`
   (`6e89ae6eb779c543a617a7cffd4277a278573f27`)
2. `Protocol-Guild/PayD#617`
   (`9050da261cec5ea97c49bfe40ff9b631ee5da17c`)

They demonstrate the exact four-section output contract against two unrelated
production diffs rather than synthetic snippets.
