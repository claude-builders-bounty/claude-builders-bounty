# generate-changelog — structured CHANGELOG from git history

A Claude Code skill **and** a plain bash/python tool that generates a
structured `CHANGELOG.md` section from a project's git history: it takes
the commits since the last git tag and auto-categorizes them into
`Added` / `Fixed` / `Changed` / `Removed`, formatted per
[Keep a Changelog](https://keepachangelog.com).

## Setup (3 steps)

1. Copy this folder anywhere. It needs only `git` and `python3`
   (standard library only — nothing to install). For the Claude Code
   skill, copy it into your project's `.claude/skills/` instead.
2. `cd` into the git repository you want a changelog for.
3. Run it: `bash changelog.sh --prepend CHANGELOG.md` — or, inside
   Claude Code with the skill installed, just run `/generate-changelog`.

## Usage

```bash
bash changelog.sh                                  # since last tag, printed to stdout
bash changelog.sh --version 1.4.0                  # title the section with a version
bash changelog.sh --prepend CHANGELOG.md           # insert at the top of CHANGELOG.md
bash changelog.sh --tag v1.2.0 --to v1.3.0 \
     --version 1.3.0 --date 2026-04-01             # document an existing release range
bash changelog.sh --repo /path/to/repo             # target another repository
```

## How categorization works (deterministic, no AI guessing)

1. A leading **remove / delete / drop** verb in the subject → `Removed`
   (so `fix: remove broken cache` lands in Removed — the removal is the
   notable change).
2. Conventional Commits type: `feat` → `Added`, `fix` → `Fixed`,
   anything else (`refactor`, `perf`, `docs`, `chore`, …) → `Changed`.
3. Imperative keyword fallback: add/introduce/create/implement →
   `Added`; fix/resolve/correct/patch → `Fixed`.
4. A commit whose only effect is deleting files → `Removed`.
5. Everything else → `Changed`.

Conventional scopes are preserved and bolded (`fix(auth): …` renders as
"**auth:** …"). Merge commits are excluded. A repository with no tags
is handled gracefully (all commits up to HEAD are used).

## Tests

```bash
python3 tests/test_changelog.py   # 12 tests, all passing
```

The suite builds throwaway git repositories with tagged, categorized
commits (including edge cases: a removal verb inside a `fix:` commit, a
pure-deletion commit, a tag-less repo) and verifies the generated
sections, category order, `--prepend` behavior, and the CLI end to end.

## Sample output (real GitHub repo)

Generated 2026-11-09 against a fresh clone of
[pallets/itsdangerous](https://github.com/pallets/itsdangerous):

- [`samples/sample-itsdangerous-unreleased.md`](samples/sample-itsdangerous-unreleased.md)
  — `bash changelog.sh --repo itsdangerous` (commits since tag `2.2.0`).
- [`samples/sample-itsdangerous-2.2.0.md`](samples/sample-itsdangerous-2.2.0.md)
  — the real 2.2.0 release range (`--tag 2.1.2 --to 2.2.0`): the tool
  files "Remove SLSA provenance"-era cleanups, typing work under
  Changed, and link/lint fixes under Fixed, matching how the project
  itself described that release.

## Acceptance criteria (issue #1) — how this build meets each

| Criterion | Evidence |
|---|---|
| Works via `/generate-changelog` command or `bash changelog.sh` | **Both.** `SKILL.md` (name: `generate-changelog`) gives the slash command; `bash changelog.sh` works standalone |
| Fetches commits since the last git tag | `git describe --tags --abbrev=0`, then `git log <tag>..HEAD`; verified by test (`test_last_tag_is_used`) |
| Auto-categorizes into Added / Fixed / Changed / Removed | Deterministic rules above; per-category tests assert placement, including edge cases |
| Outputs a properly formatted `CHANGELOG.md` | Keep a Changelog section format; `--prepend` inserts into an existing file under its header |
| Tested on a real GitHub repo (sample output in the PR) | Two samples from pallets/itsdangerous in `samples/`, generated with the exact commands above |
| README with setup instructions in 3 steps or fewer | "Setup (3 steps)" at the top of this file |

## Honest limitations

- Categorization is heuristic: a vaguely worded commit ("misc updates")
  lands in Changed. The skill instructions tell Claude to flag suspect
  entries to the user rather than silently rewrite them.
- Only the first line (subject) of each commit is used; body text is
  ignored so generated entries stay one line each.
