# generate-changelog

Turn git history into a [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
`CHANGELOG.md` — as a Claude Code skill (`/generate-changelog`) or as a plain
shell script (`bash changelog.sh`).

No runtime, no packages, no config: bash, git, awk, sed.

## Setup

**1. Copy the skill into your project** (or `~/.claude/skills/` to get it everywhere):

```bash
cp -r skills/generate-changelog .claude/skills/
```

**2. Generate a changelog** — in Claude Code:

```
/generate-changelog
```

...or straight from a shell, in any git repo:

```bash
bash .claude/skills/generate-changelog/changelog.sh --version 1.4.0
```

**3. Read the diff to `CHANGELOG.md` and commit it.**

## What it does

- Reads commits between the **last git tag** and `HEAD` (`--since` / `--to` to override).
- Sorts them into **Added / Changed / Deprecated / Removed / Fixed / Security**,
  in Keep a Changelog order:
  - **Conventional Commits** by type — `feat` → Added, `fix` → Fixed,
    `perf`/`refactor`/`revert` → Changed, `remove` → Removed, `deprecate` →
    Deprecated, `security` → Security.
  - **Anything else** by the subject's leading verb — `Added …` → Added,
    `Fixed …` → Fixed, `Removed …` → Removed, everything else → Changed. Only the
    first word counts, so a "fix" in the middle of a sentence can't drag the
    entry into the wrong section.
- Drops `docs`, `chore`, `ci`, `build`, `test` and `style` commits (`--all` keeps them),
  along with merge commits and duplicate subjects left by cherry-picks.
- Marks breaking changes (`feat!:` or a `BREAKING CHANGE:` trailer) with **BREAKING**.
- Links each entry to its PR when the subject ends in `(#123)`, otherwise to its
  commit, using the `origin` remote (`--repo` to override; plain text with no remote).
- Dates a release from its tag, so re-generating an old section reproduces it.
- Inserts above the newest release and leaves the rest of the file untouched.
  Writing a version that already exists is refused rather than duplicated.

## Options

```
--since <ref>     Start of the commit range (default: last tag reachable from HEAD)
--to <ref>        End of the commit range (default: HEAD)
--version <name>  Release heading (default: tag at HEAD, else "Unreleased")
--output <file>   File to create or update (default: CHANGELOG.md)
--repo <url>      Repository URL used for links (default: the "origin" remote)
--stdout          Print the new section instead of writing to a file
--all             Also include docs/chore/ci/build/test/style commits
-h, --help        Show this help
```

```bash
./changelog.sh                          # add an "Unreleased" section to CHANGELOG.md
./changelog.sh --version 1.4.0          # cut a dated release section
./changelog.sh --since v1.0.0 --stdout  # preview a range without touching the file
```

## Sample output

[`samples/anthropic-sdk-python.md`](samples/anthropic-sdk-python.md) is verbatim
output from a real repository — two releases of
[anthropics/anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python),
generated at tag `v0.122.0`:

```bash
git clone https://github.com/anthropics/anthropic-sdk-python && cd anthropic-sdk-python
../skills/generate-changelog/changelog.sh --to v0.121.0 --output CHANGELOG.md
../skills/generate-changelog/changelog.sh --output CHANGELOG.md
```

```markdown
## [v0.122.0] - 2026-08-13

> 28 commits since `v0.121.0` · [full diff](https://github.com/anthropics/anthropic-sdk-python/compare/v0.121.0...v0.122.0)

### Added

- **api**: add output_behavior to dream creation (create a new memory store or update the input store in place) ([`1571dddf`](https://github.com/anthropics/anthropic-sdk-python/commit/1571dddf))

### Fixed

- **client**: keep token exchange bound per client across copy() ([#388](https://github.com/anthropics/anthropic-sdk-python/pull/388))
- **bedrock,aws**: run SigV4 signing off the event loop in async clients ([#334](https://github.com/anthropics/anthropic-sdk-python/pull/334))
```

The 28 commits in that range produced 17 entries; the other 11 were `chore` and
`docs`.

## Tests

```bash
bash tests/run_tests.sh
```

50 assertions over throwaway git repos built in a temp directory — categorization,
tag ranges, breaking changes, PR links, file insertion, and the error paths
(unknown ref, empty range, missing option value, not a git repo). Nothing outside
the temp directory is touched.

## Using it in CI

```yaml
- uses: actions/checkout@v4
  with: { fetch-depth: 0 }          # tags and history are required
- run: bash .claude/skills/generate-changelog/changelog.sh --version ${{ github.ref_name }}
```
