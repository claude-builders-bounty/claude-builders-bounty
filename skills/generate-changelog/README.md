# Generate a structured changelog

Python 3.8+ and Git; no API key or dependencies.

## Setup (3 steps)

1. Copy `changelog.py` and `changelog.sh` into your Git repository.
2. Ensure Git and Python 3 are installed.
3. Run `bash changelog.sh` from your repository root (or `python3 changelog.py --repo /path/to/repo`).

Writes `CHANGELOG.md` with Added, Fixed, Changed and Removed sections from commits since the nearest reachable tag. Conventional Commits are categorized by type; other messages use simple subject classification. Without tags, all non-merge commits are used. Existing output is overwritten; use `--stdout` to preview first.

## Verification

The included unit tests use actual temporary Git repositories. Run `python3 -m unittest discover -s tests -v`.

The real-public-repository demonstration is in `real_repo_demo.sh`. It clones the public [pallets/itsdangerous](https://github.com/pallets/itsdangerous) repository, runs the generator against that Git history, checks that the generated changelog is nonempty and properly headed, and prints the output. The GitHub Actions workflow `.github/workflows/changelog-real-repo-demo.yml` executes both unit tests and this public-repository demonstration; its successful run uploads `CHANGELOG.real-repo.md` and `provenance.txt` as the `changelog-real-public-repo` artifact. The fixture-based `sample_CHANGELOG.md` is illustrative, not a claim to contain public-repository history.

The demonstration only reads the upstream repository and does not modify it. Acceptance and payout depend on the bounty maintainers.
