# Subscription-only Claude Code PR reviewer

A standalone implementation for Claude Builders Bounty issue #4. It outputs a structured Markdown review of a real public GitHub PR without posting anything.

## Setup

Requires Python 3.10+, GitHub CLI (`gh`) with access to the selected PR, and the official Claude Code CLI with an existing authenticated Claude subscription. This implementation deliberately does not use API-key billing, install packages, purchase a plan, or create accounts.

1. Verify `python3 --version`, `gh auth status`, and `claude --version`.
2. If needed, personally authenticate the existing subscription with `claude auth login --claudeai`. Never paste passwords, OTPs, or authorization codes into an issue or review.
3. From the repository root, expose the executable:
   ```sh
   export PATH="$PWD/agents/subscription-pr-reviewer:$PATH"
   ```

## Usage

```sh
claude-review --pr https://github.com/pallets/flask/pull/6176 --output review.md --evidence-dir evidence
```

For a non-PATH installation, add `--claude-bin /path/to/claude`. Output paths must refer to locations you intend to write. Do not point them at repository metadata or unrelated files.

The command captures the real unified diff and PR base/head revisions, refuses an invalid/empty or >150,000-byte diff, and checks that the revisions remained stable during capture. It invokes the named `structured-pr-reviewer` Claude Code agent through an explicit in-memory agent definition, and validates:

- `## Summary of changes`: 2–3 English sentences;
- `## Identified risks`: a nonempty Markdown bullet list;
- `## Improvement suggestions`: a nonempty Markdown bullet list;
- `## Confidence score`: exactly Low, Medium, or High.

To reduce sentence-boundary ambiguity, the prompt requests complete English sentences without abbreviations. Format validation is a syntactic gate, not proof that a model's findings are correct.

`--prepare` fetches the diff and outputs only the prompt. It does **not** run Claude or count as a completed review. `--evidence-dir` records the exact input diff, URL, base/head SHAs, capture time, input/review SHA-256 and sanitized model provenance. `--output` writes the review; otherwise it is printed to stdout.

## Safety and scope

- Diff text is quoted untrusted data. It is never interpolated into a shell command or executed.
- Claude is invoked with no tools, an empty strict MCP configuration, hooks disabled, no user/project/local settings sources, and no session persistence. No permission-bypass flags are used.
- Existing subscription authentication is checked before inference. API/cloud billing environment overrides are removed from the child process; there is no API-key fallback.
- There is no code path for posting a comment, submitting a review, merging a PR, claiming a bounty or changing account/billing settings.
- The process fetches public GitHub diff data and sends that data to the user's authorized Claude subscription. It does not check out or run reviewed repository code.
- Findings are diff-only, model-generated analysis; confidence is a model assessment, not a correctness guarantee. Full implementation context and upstream tests are not executed. Automated review should not replace maintainer judgment.

The portable agent definition is included in `.claude/agents/structured-pr-reviewer.md`. The CLI supplies the same agent prompt explicitly rather than depending on global agent discovery.

## Verification

```sh
cd agents/subscription-pr-reviewer
python3 -m unittest -v test_reviewer.py
```

14 local tests pass. They cover strict PR URLs, untrusted-data framing, required headings/order, confidence, nonempty sections, bullet lists and 2–3 sentence summaries. Seven new format regressions were observed failing before the validator fix, then passing afterward. The local tests are separate from actual model inference.

Two **real Claude Code** end-to-end runs were completed on 2026-11-07 through existing Pro subscription authentication:

- [Flask PR #6176](https://github.com/pallets/flask/pull/6176): [review](samples/flask-6176.md), [input](samples/flask-6176/input.diff), [execution provenance](samples/flask-6176/execution.json).
- [Flask PR #6168](https://github.com/pallets/flask/pull/6168): [review](samples/flask-6168.md), [input](samples/flask-6168/input.diff), [execution provenance](samples/flask-6168/execution.json).

The requested model alias was `sonnet`; the actual CLI reports `claude-sonnet-5-5` in both runs. Those literal observed identifiers are preserved. Samples are not mocked or templated reviews. Each saved review's structure and SHA-256, and each input's SHA-256, were independently checked. No comments were posted on either Flask PR.

Third-party Flask diff excerpts retain their upstream BSD-3-Clause notice in [FLASK_LICENSE.txt](samples/FLASK_LICENSE.txt); the input source revisions are recorded with each sample. This contribution otherwise follows the host repository's existing MIT license.

## Acceptance mapping

- Required `claude-review --pr <URL>` CLI: executable `claude-review`.
- Native Claude Code agent: explicit `--agents` / `--agent structured-pr-reviewer` invocation, with portable agent documentation.
- Four structured sections and summary length: validator + 14 tests.
- At least two real GitHub PR runs: both committed samples and input/provenance files.
- Setup/usage: this README.

CLI is the issue's selected supported route; no GitHub Action is claimed or required by the issue's CLI **or** Action choice.
