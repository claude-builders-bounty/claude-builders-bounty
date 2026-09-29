# Structured Changelog Generator

A dependency-free Python generator with a Bash entry point for bounty #1. It reads non-merge commits since the latest reachable Git tag and writes a deterministic `CHANGELOG.md` grouped into `Added`, `Fixed`, `Changed`, and `Removed`.

## Setup — 3 steps

1. Copy `changelog.py` and `changelog.sh` into your project.
2. Make the wrapper executable: `chmod +x changelog.sh`.
3. Run `./changelog.sh` from the target repository.

By default, the output is `CHANGELOG.md` in the target repository. No network access, API key, package install, or build step is required.

## Usage

```bash
# Current repository, full latest-tag..HEAD history
./changelog.sh

# Another repository
./changelog.sh --repo /path/to/repo

# Preview without writing
./changelog.sh --repo /path/to/repo --stdout

# Custom output path
./changelog.sh --repo /path/to/repo --output docs/CHANGELOG.md
```

`--max-commits N` is an optional review/sample convenience. The default has no limit and processes the complete non-merge range after the latest reachable tag.

### Categorization

Conventional-style commit prefixes are recognized, with plain-English fallbacks:

- **Added:** `feat`, `feature`, `add`, `new`, `create`, `introduce`
- **Fixed:** `fix`, `bugfix`, `hotfix`, `repair`
- **Removed:** `remove`, `delete`, `drop`
- **Changed:** all other commits, including `docs`, `refactor`, `perf`, `chore`, `build`, `ci`, `test`, and uncategorized subjects

Scopes and breaking markers work as expected, e.g. `feat(ui)!: add new shell` is `Added` and `fix(core)!: prevent crash` is `Fixed`.

If the repository has no tag yet, the generator uses all non-merge history through `HEAD`. If the latest tag has no later commits, it writes a valid empty-range changelog rather than failing.

## Tests

```bash
python3 -m unittest discover -s issue-1-changelog-generator/tests -v
```

The tests create temporary real Git repositories, make commits and tags, and verify tag-range selection, all four categories, untagged repositories, optional sample limiting, and an empty post-tag range.

## Real-repository sample

`sample/CHANGELOG.rustchain.md` was generated against the public `Scottcjn/Rustchain` repository clone. The repository had hundreds of post-tag commits, so the checked-in review sample intentionally uses:

```bash
./changelog.sh \
  --repo /path/to/Rustchain \
  --max-commits 25 \
  --output /path/to/sample/CHANGELOG.rustchain.md
```

The limit is only for keeping the proof artifact reviewable; ordinary execution has no commit limit.
