# generate-changelog

> Bash script and Claude Code skill that builds a structured `CHANGELOG.md` from git commit history.

Bounty submission for [issue #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1).

## Quick start

1. `chmod +x changelog.sh`
2. `bash changelog.sh` (use `--version 1.2.0` to set the release header, or `--preview` to print without writing)
3. Open the generated `CHANGELOG.md`

Sample output generated from this repository: [`samples/CHANGELOG.sample.md`](samples/CHANGELOG.sample.md).

The generator fails closed when the repository has no commits or `--since` does not resolve to an ancestor of `HEAD`, preventing misleading empty release output.

## Claude Code

Copy this folder to `.claude/skills/generate-changelog/` to enable the `/generate-changelog` command.

## Tests

```bash
bash skills/generate-changelog/tests/test_changelog.sh
```

Unknown commit categories appear under **Uncategorized** with a manual-review note; they are never silently assigned to Changed. Literal backslash sequences are preserved. Shallow Git histories are rejected before output is written; fetch full history and tags before retrying.

`--append` is idempotent for a given `--version`: rerunning a release replaces that generated version section instead of duplicating it, while older release history is preserved.

Automatic release boundaries follow the first-parent history, so a tag on a merged topic branch cannot hide unreleased mainline changes. Commit collection still includes non-merge commits from merged branches. Use `--since <tag>` to select a different ancestor explicitly.
