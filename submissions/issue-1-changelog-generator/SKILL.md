---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a repo's git history since the last tag, bucketed into Added / Changed / Fixed / Removed. Use when the user asks to generate, update, or refresh a changelog or release notes.
---

# Generate Changelog

Generates a Keep-a-Changelog–formatted `CHANGELOG.md` from git history. The heavy
lifting is done by `changelog.sh` (in this skill's directory) so results are
deterministic and reproducible.

## Steps

1. Confirm the working directory is a git repository (`git rev-parse --git-dir`).
2. Run the script from the repo root:
   ```bash
   bash changelog.sh
   ```
   - It uses commits since the most recent tag, or the full history if untagged.
   - Override the range with `--since <ref>` (e.g. `--since v1.2.0`).
   - Preview without writing: `bash changelog.sh --stdout`.
   - Custom file: `bash changelog.sh -o RELEASE_NOTES.md`.
3. Open the generated `CHANGELOG.md`, then:
   - Move the `## [Unreleased]` heading to the version being released if a release
     is being cut (e.g. `## [1.3.0] - 2026-07-01`).
   - Tighten any wording that reads awkwardly — the script categorizes from commit
     subjects, so a vague commit yields a vague line. Prefer editing the commit
     history's conventions over hand-editing the changelog long-term.

## How it categorizes

- Conventional-Commit types: `feat`→**Added**, `fix`→**Fixed**,
  `revert`/`remove`/`deprecate`→**Removed**, `perf`/`refactor`/`style`/`build`→**Changed**.
- `chore`/`docs`/`test`/`ci` and pure version-bump commits are omitted as noise.
- Non-conventional subjects fall back to keyword sniffing (add/fix/remove/…),
  else land in **Changed**.
