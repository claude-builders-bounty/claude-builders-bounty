# Claude PR Review Agent

This contribution implements the `$150` PR-reviewer bounty in issue #4.

## Install

From the repository root:

```bash
python3 -m pip install --user .
```

Or run the included entry point directly:

```bash
chmod +x bin/claude-review
```

## Use

```bash
bin/claude-review --pr https://github.com/owner/repo/pull/123
```

The command downloads only the public diff, passes that text to Claude Code in
non-interactive one-turn mode, and prints a structured Markdown review. It does
not clone, execute, or modify the target repository. Set `GITHUB_TOKEN` only if
GitHub rate limiting is encountered. Set `CLAUDE_BIN` if the `claude` executable
is not on `PATH`.

The output contains:

- a two-to-three sentence summary;
- severity-labelled risks with locations when visible;
- actionable improvement suggestions; and
- a Low/Medium/High confidence score.

To publish the generated Markdown as a pull-request comment, pass a GitHub
token explicitly (or set `GITHUB_TOKEN`) together with `--post-comment`:

```bash
GITHUB_TOKEN=ghp_example bin/claude-review \
  --pr https://github.com/owner/repo/pull/123 --post-comment
```

The comment is never posted unless `--post-comment` is supplied. Use a token
with only the minimum repository issue-comment permission needed for the target
repository.

## Verification

```bash
python3 -m unittest discover -s tests -v
```

The `samples/` directory contains two manually checked Markdown examples based
on public pull requests. Live generation requires an authenticated Claude Code
installation, which is deliberately not bundled in this repository.
