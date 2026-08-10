# generate-changelog

Generate a structured `CHANGELOG.md` from a project's git history.
_Submission for [issue #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)._

Collects every commit since the last git tag, sorts them into **Added**,
**Changed**, **Fixed** and **Removed**, and writes a
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) section on top of the
existing file. Ships as both a Claude Code skill (`/generate-changelog`) and a
standalone bash script (`bash changelog.sh`).

Requires **git** and **bash** — nothing else. Works on Linux, macOS, and Windows
via Git Bash.

## Setup

1. Copy `changelog.sh` to your project root, and the
   `.claude/skills/generate-changelog/` folder into your project (or into
   `~/.claude/skills/` to have it available in every project).
2. Make it executable — `chmod +x changelog.sh` (skip on Windows).
3. Run `bash changelog.sh --stdout` to preview, or `/generate-changelog` inside
   Claude Code.

## Usage

```bash
bash changelog.sh                  # since the last tag → CHANGELOG.md
bash changelog.sh --stdout         # preview only, writes nothing
bash changelog.sh --release v1.2.0 # name the version explicitly
bash changelog.sh --from v1.0.0 --to v1.1.0 --release v1.1.0
bash changelog.sh -C ../other-repo -o ../other-repo/CHANGELOG.md
```

| Option              | Effect                                                          |
| ------------------- | --------------------------------------------------------------- |
| `-C, --repo <path>` | Repository to read (default: current directory)                  |
| `-f, --from <ref>`  | Start of the range (default: most recent tag)                    |
| `-t, --to <ref>`    | End of the range (default: `HEAD`)                               |
| `-o, --output <f>`  | File to write (default: `CHANGELOG.md`)                          |
| `-r, --release <n>` | Version heading (default: the tag on `--to`, else `Unreleased`)  |
| `--stdout`          | Print the section, write nothing                                 |
| `--authors`         | Append the commit author to every entry                          |
| `--no-chore`        | Drop `chore` / `ci` / `build` / `style` / `test` commits          |
| `--force`           | Write even if that version heading already exists                |
| `-h, --help`        | Full help                                                        |

## How commits are categorised

The conventional-commit type is read first; when the type is uninformative
(`chore`, `refactor`, `docs`, …) or absent, the leading verb of the subject
decides. That two-stage rule is what puts `chore: drop legacy polyfill` under
**Removed** rather than **Changed**.

| Section     | Matches                                                                            |
| ----------- | ----------------------------------------------------------------------------------- |
| **Added**   | `feat`, `feature` — or add / adds / introduce / implement / create / support / new    |
| **Fixed**   | `fix`, `bugfix`, `hotfix`, `patch` — or fix / correct / resolve / repair              |
| **Removed** | `revert`, `deprecate` — or remove / delete / drop / strip / retire                    |
| **Changed** | everything else                                                                       |

Merge commits are skipped. `feat!:` or a `BREAKING CHANGE` body prefixes the
entry with **BREAKING**. Entries link to the commit on the `origin` remote when
there is one, and fall back to a bare short SHA when there isn't.

## Behaviour worth knowing

- **Non-destructive.** A new section is inserted above the existing ones; older
  releases in `CHANGELOG.md` are preserved. If the version heading is already
  present the script exits non-zero instead of duplicating it.
- **No tags yet?** The range falls back to the whole history.
- **`--to` on a tag** starts from the *previous* tag, so `--to v1.1.0` yields
  exactly the v1.1.0 release rather than an empty range.
- The script never commits, tags, or pushes.

## Sample output

[`examples/CHANGELOG.sample.md`](../examples/CHANGELOG.sample.md) — five release
sections generated verbatim against
[anthropics/anthropic-sdk-typescript](https://github.com/anthropics/anthropic-sdk-typescript).
The header of that file lists the exact commands used, so it can be reproduced
end to end.

## Validation performed

| Case | Result |
| --- | --- |
| Real GitHub repo (`anthropic-sdk-typescript`, 5 releases) | see sample |
| Repo with no tags | falls back to full history |
| Repo with no `origin` remote | entries degrade to bare short SHA |
| `feat!:` / `BREAKING CHANGE` body | entry marked **BREAKING** |
| Re-run with an existing version heading | refuses, exits 1, `--force` overrides |
| Insert into a populated `CHANGELOG.md` | prior sections preserved |
| Unknown ref / missing directory | clean error message, exit 1 |
| `bash -n changelog.sh` | passes |
