## Summary of changes
This PR introduces a pure‑Bash changelog generator that parses the Git history since the latest tag (or a user‑supplied reference). It classifies commits into the Keep‑a‑Changelog sections **Added**, **Fixed**, **Changed**, and **Removed** using Conventional Commit keywords with a keyword fallback. The new skill is documented in `SKILL.md`, a README explains usage, and a sample output is provided.

## Identified risks
- **Tag‑lookup logic** – `git describe --tags --abbrev=0` fails when no tags exist, but the script falls back to `HEAD`. The fallback comment says “Include all commits if no tag exists”, yet the `--all` flag is ignored because `RANGE="HEAD"` is used in both branches. This could lead to confusion when the repository has no tags and the user expects all commits to be included.
- **Missing `--no-merges` handling** – The README mentions that merge commits are skipped with `--no-merges`, but the script never passes `--no-merges` to `git log`. As a result, merge commits will appear in the generated changelog.
- **Date formatting** – The script extracts the commit date using `git show -s --format=%cd --date=short`, which may produce different locales or time‑zone formats depending on the user’s Git configuration. This could break the deterministic output expected by CI pipelines.
- **Error handling for `--since`** – If the user supplies a non‑existent reference to `--since`, `git log` will exit with a non‑zero status, causing the script to abort. A more graceful error message would improve UX.
- **Hard‑coded output path** – The default output file is `CHANGELOG.md` in the current directory, which may overwrite an existing file unintentionally. A safety check or a `--force` flag could mitigate accidental data loss.

## Improvement suggestions
- **Clarify tag‑lookup behavior** – Update the logic to explicitly handle the “no tags” case and document the difference between `--all` and the default behavior. Consider setting `RANGE="HEAD"` only when `--all` is true, otherwise use `git rev-list --max-parents=0 HEAD` to get the first commit.
- **Add `--no-merges` option** – Introduce a `--no-merges` flag that passes `--no-merges` to `git log`. This aligns the script with the README and prevents merge commits from cluttering the changelog.
- **Locale‑independent date** – Use `git show -s --format=%cd --date=format:%Y-%m-%d` to guarantee a consistent ISO‑8601 date format regardless of user settings.
- **Validate `--since` reference** – Before constructing `RANGE`, check that the reference exists (`git rev-parse --verify "$SINCE" 2>/dev/null`). If it does not, print a clear error message and exit with status 2.
- **Protect existing output** – Add a check that `OUTPUT` does not already exist unless `--force` is supplied. This prevents accidental overwrites during CI runs.
- **Refactor commit classification** – Extract the classification logic into a dedicated function (`classify_commit()`) to make the code easier to test and maintain. This also allows adding new keyword mappings without cluttering the main loop.
- **Add unit‑style tests** – Although Bash scripts are hard to unit‑test, consider adding a small test harness that runs the script against a temporary repository and verifies the output structure.

## Confidence score
**Medium**

The change is straightforward and well documented, but the script contains a few logical gaps (tag handling, merge commits, date formatting) that could surface in edge cases. The overall intent is clear, and the added documentation is helpful, but the implementation would benefit from the improvements above.