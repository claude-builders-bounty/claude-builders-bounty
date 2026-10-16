# Real public repository verification

The included `CHANGELOG_FROM_PUBLIC_REPO.md` was produced by the supplied
`tests/verify_public_repo.sh` against the publicly available Git repository
[Click](https://github.com/pallets/click) on 2026-10-16 UTC.

- Source repository: `https://github.com/pallets/click.git`
- Latest reachable tag: `8.5.0`
- Commits since that tag: 49 (including merge commits)
- Non-merge commit subjects included in the generated changelog: 25
- Generated sections: Added, Fixed, Changed, Removed
- Reported on Git Bash for Windows: `PUBLIC REPO TEST PASSED`

This is a snapshot of the repository when the test ran, not a claim that its
latest tag or commit counts will remain unchanged.

## Reproduce the check

From `tools/generate-changelog/` with Git, Bash and network access:

```bash
bash tests/verify_public_repo.sh
```

The script clones Click into a temporary folder, runs the generator, and
updates the local sample file. It makes no commits or changes to the remote.
