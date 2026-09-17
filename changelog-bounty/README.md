# Changelog bounty

Small, deterministic generator for a Markdown `CHANGELOG.md` from Git history.

## Install and run

1. Copy this directory (Python 3.9+ and Git are required).
2. From the repository to document, run `bash /path/to/changelog-bounty/changelog.sh`.
3. Review the generated `CHANGELOG.md` (or pass `--output PATH`).

The range is `latest-tag..HEAD`. Without tags, the fallback is all commits and
is stated in the heading. Messages with conventional prefixes are classified;
ambiguous messages are conservatively placed in `Changed` without inventing
content. A configured `origin` GitHub remote enables commit links.

## Verify

Run `python -m unittest discover -s tests -v` from this directory. The test
creates a temporary real Git repository and checks both tagged and tagless
history. A checked-in example is in [`sample/CHANGELOG.md`](sample/CHANGELOG.md).
