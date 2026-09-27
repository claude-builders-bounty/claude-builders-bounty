# Generate a structured changelog

This script creates an Unreleased section for a repository's latest reachable
Git tag. It reads local Git metadata only; it does not fetch, contact an API,
or read files from the repository.

## Use it

1. Copy this folder into the target repository.
2. From that repository, run:

       bash tools/generate-changelog/changelog.sh

3. Review and commit CHANGELOG.md. If it already exists, add --force only after
   you have saved or reviewed its current contents.

The output groups commit subjects under Added, Fixed, Changed, and Removed.
Conventional Commit prefixes such as feat:, fix:, and refactor: are recognized;
plain subjects beginning with add, fix, remove, or similar verbs are handled
too. Subjects with no recognizable type go under Changed. Merge commits are
omitted to avoid listing the same work twice.

If no reachable tag exists in the checkout, the script uses all available
non-merge history. In a shallow clone, that means only the history present
locally. Use --stdout to preview without writing. Use --repo PATH to select a
repository and --output PATH to select a destination.

The categorization follows commit subjects and can be wrong if a subject is
misleading. Review generated release notes before publishing them.

## Real repository sample

[`examples/sample-CHANGELOG.md`](examples/sample-CHANGELOG.md) was generated
with the shell wrapper from the public `siddhss5/labdata` GitHub repository.
The exact source revision and command are recorded in
[`examples/README.md`](examples/README.md).

## Verify

From this folder, run:

    python3 -B -m unittest -v
