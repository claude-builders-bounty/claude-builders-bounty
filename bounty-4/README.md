# claude-review

`claude-review` fetches a GitHub pull request, sends its metadata and diff to
Claude Code, and prints a concise structured Markdown review. It can also post
the validated review back to the PR.

## Requirements

- Python 3.10+
- GitHub CLI (`gh`) authenticated for the repository being reviewed
- Claude Code CLI (`claude`) installed and authenticated

No Python packages or `jq` are required.

## Install

```bash
cd bounty-4
./install.sh
export PATH="$HOME/.local/bin:$PATH"
```

The installer creates a symlink at `~/.local/bin/claude-review`.
## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
claude-review --pr https://github.com/owner/repo/pull/123 --post
```

Use `--claude-bin /path/to/claude` when Claude Code is not on `PATH`.

## Review contract

Every successful review is validated before it is printed or posted:

- `## Summary` — exactly 2–3 sentences requested from Claude.
- `## Risks` — evidence-based bullet list.
- `## Improvement suggestions` — actionable bullet list.
- `## Confidence` — exactly `Low`, `Medium`, or `High`.

The prompt tells Claude not to invent runtime behavior, tests, or
vulnerabilities. Reviews missing a required section fail instead of posting
partial output.
## Large PRs

The complete diff is used up to 120,000 UTF-8 bytes by default. Larger diffs
are explicitly marked as truncated in the prompt, which instructs Claude to
lower confidence when omitted context may matter.

Override the limit when needed:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 \
  --max-diff-bytes 200000
```

## Posting safety

`--post` only runs after the generated Markdown passes the output validator.
The review body is passed to `gh pr comment --body-file`, avoiding shell
interpolation of model output.

## Verification

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile claude_review.py
```
The tests cover URL validation, UTF-8-safe diff truncation, prompt structure,
review validation, CLI output, and the `--post` path without making network or
Claude calls.

Two real GitHub PRs were fetched with `gh pr view` / `gh pr diff` and reviewed
using the same prompt contract:

- `samples/pr-8.md` — claude-builders-bounty PR #8.
- `samples/pr-10.md` — claude-builders-bounty PR #10.

These samples are committed so reviewers can inspect the expected output
format without needing Claude credentials.

## Design choices

The tool uses `gh` rather than GitHub API tokens directly, Python's JSON
parser rather than `jq`, and a temporary body file when posting. Claude Code
is invoked non-interactively with `claude -p <prompt>`; set `CLAUDE_BIN` or
`--claude-bin` for installations with a different executable name.
