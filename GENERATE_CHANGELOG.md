# Generate a changelog

Requires Git, Bash, and Python 3.9+. No third-party packages or API keys.

1. Copy `changelog.sh` and `generate_changelog.py` into your project (keep them together).
2. Ensure local history and tags are complete: for a shallow clone, run `git fetch --unshallow --tags`; otherwise use `git fetch --tags` when needed.
3. Run `bash changelog.sh` in the target repository, then review `CHANGELOG.md` before publishing it.

You can instead run `bash /path/to/changelog.sh --repo /path/to/project --output /path/to/preview.md`. The output parent directory must already exist. `PYTHON` can select a Python executable; on Windows use Git Bash, or run `python generate_changelog.py` directly.

The generator reads non-merge commits after Git's nearest reachable tag (`git describe --tags --abbrev=0`). This includes lightweight and annotated tags. No tags means all commits; shallow clones are rejected to avoid incomplete release boundaries. It does not make network requests or change Git history.

Conventional `feat`/`feature`/`add` subjects go to Added; `fix`/`bugfix` go to Fixed; `remove`/`removed`/`delete` go to Removed. All other subjects go to Changed. Non-conventional subjects use their first word with the same mapping. Scopes and breaking-change markers remain in the text. This is a deterministic first draft, not semantic analysis: review categories and remove internal-only entries yourself.

Each run replaces the existing Unreleased section, including any manual edits inside that section. Release sections and the introduction are preserved. Running again with unchanged history produces the same output. Use `--output` for a preview if Unreleased contains notes you need to keep.

Run integration tests with `python -m unittest discover -s tests -v`. They create temporary real Git repositories and cover tag boundaries, unrelated tags, four categories, Unicode, release preservation, repeatability, empty repositories, and shallow history.

The generated public-repository example and its pinned source revision are under `examples/`.
