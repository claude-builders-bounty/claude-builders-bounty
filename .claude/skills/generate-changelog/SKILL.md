---
name: generate-changelog
description: Generate or update a structured CHANGELOG.md from the git history of the current repository, grouping the commits since the last tag into Added / Fixed / Changed / Removed. Use when the user asks to write, refresh, or preview a changelog, cut a release note, or summarise what changed since the last tag.
---

# Generate a structured CHANGELOG

Turn the commits made since the last git tag into a [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
section and write it at the top of `CHANGELOG.md`.

The heavy lifting is done by `changelog.sh` at the repository root — call it
rather than reimplementing the log parsing.

## Steps

1. **Check the ground.** Confirm you are in a git work tree and see what the
   range will be:

   ```bash
   git rev-parse --is-inside-work-tree && git describe --tags --abbrev=0
   ```

   If there is no tag, the script falls back to the entire history — tell the
   user, because that first run is usually large.

2. **Preview.** Never write blind; render the section to the terminal first:

   ```bash
   bash changelog.sh --stdout
   ```

3. **Show the preview to the user and let them react.** Point out anything that
   landed in a category that looks wrong, and mention the useful switches:
   `--release v1.2.0` to name the version, `--no-chore` to drop
   chore/ci/build/style/test noise, `--authors` to credit each commit,
   `--from <ref> --to <ref>` for an explicit range.

4. **Write it.** Once the preview looks right:

   ```bash
   bash changelog.sh --release v1.2.0
   ```

   The new section is inserted above the existing ones; nothing already in
   `CHANGELOG.md` is lost. If that version heading is already present the
   script refuses and exits non-zero — re-run with `--force` only when the user
   genuinely wants a duplicate.

5. **Polish, don't regenerate.** Commit subjects are terse by nature. If the
   user wants nicer prose, edit the generated entries in `CHANGELOG.md` with
   the Edit tool — keep the commit links intact, and keep every entry under the
   heading the script chose unless the user asks to move it.

## Category rules

`changelog.sh` reads the conventional-commit type first, then falls back to the
leading verb of the subject:

| Section     | Matches                                                        |
| ----------- | -------------------------------------------------------------- |
| **Added**   | `feat`, and subjects starting with add / introduce / implement / create / support |
| **Fixed**   | `fix`, `hotfix`, `patch`, and subjects starting with fix / correct / resolve / repair |
| **Removed** | `revert`, `deprecate`, and subjects starting with remove / delete / drop / retire |
| **Changed** | everything else — `refactor`, `perf`, `docs`, `chore`, `ci`, ... |

Merge commits are always skipped. `feat!:` or a `BREAKING CHANGE` body marks the
entry **BREAKING** in place.

## Notes

- The script only reads git and writes the output file. It never commits,
  tags, or pushes — if the user wants the changelog committed, do it as a
  separate, explicit step.
- Entries link to `<remote origin>/commit/<sha>` when an origin remote exists,
  and degrade to a bare short SHA when it does not.
- Requires bash and git only. On Windows, run it from Git Bash.
