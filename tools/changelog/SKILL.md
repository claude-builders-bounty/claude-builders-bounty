---
name: generate-changelog
description: Generate a Keep-a-Changelog-formatted CHANGELOG.md section from git history since the last tag, auto-categorized into Added / Changed / Fixed / Removed using Conventional Commits + verb-prefix heuristics. Invoke when the user asks for a changelog, release notes, or "what changed since the last release".
---

You are the **generate-changelog** skill. Your single job is to produce a tidy CHANGELOG.md update from the project's git history.

## How to run

1. Determine the project root. Default to the current working directory unless the user names a path.
2. Decide the base ref:
   - If the user named a ref (`since v1.2.3`, `since main`, `since abc123`), use it.
   - Otherwise let the script auto-detect the last tag (`git describe --tags --abbrev=0`).
3. Decide the version label for the new section:
   - If the user named a version (`v1.2.4`), use it.
   - If they said "release", suggest the next semver bump after the last tag and confirm with the user before committing to it.
   - Otherwise default to `Unreleased`.
4. Invoke the bundled script:

   ```bash
   python tools/changelog/generate_changelog.py \
     --repo <project-root> \
     --version <label> \
     --in-place
   ```

   Use `--in-place` only if the user wants the existing CHANGELOG.md updated. Otherwise omit it and capture the stdout for them to review first. Add `--repo-url https://github.com/<owner>/<repo>` so commit hashes render as clickable links.

5. After the script finishes, show the user the new section verbatim. If `--in-place` was used, also show a `git diff -- CHANGELOG.md` so they can confirm the change before committing.

## When NOT to invoke

- The repo has no git history at all — say so and stop.
- The user wants release notes for a specific GitHub release page (use the `gh release create --notes-file` pattern instead, but this skill is the generator for `--notes-file`).
- The user asks "what does my last commit do?" — that's a single-commit question, not a changelog. Answer directly without invoking the script.

## Style rules

- Don't paraphrase or rewrite the script's output — the script's render is the contract.
- If the script returns exit code 2 ("No commits to write"), tell the user there's nothing new since the base ref and stop.
- If `git` is not on PATH or the directory isn't a repo, surface the exact error from stderr.
