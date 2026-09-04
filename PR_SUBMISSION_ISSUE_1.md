# feat(skill): structured CHANGELOG generator from git history (#1)

Fixes #1 (💰 **Bounty: $50**)

## Technical Diagnosis & Summary

Maintaining changelogs manually is error-prone, inconsistent, and frequently falls out of sync with actual release commits. Without automated categorization, release notes often lump feature additions, bug fixes, refactors, and breaking changes into monolithic lists.

This pull request provides a zero-dependency, Keep-a-Changelog compliant generator available as a native Claude Code skill (`SKILL.md`), a cross-platform Python script (`changelog.py`), and a pure Bash script (`changelog.sh`):
1. Detects the latest reachable git tag automatically (or falls back to initial commit if unreleased).
2. Parses commit messages using Conventional Commits patterns (`feat:`, `fix:`, `refactor:`, `revert:`, and keyword fallbacks).
3. Auto-categorizes commits into four standardized sections: **Added**, **Fixed**, **Changed**, and **Removed**.
4. Compiles a structured, markdown-compliant changelog adhering to Keep-a-Changelog standard.

---

## Acceptance Criteria Checklist

- [x] **Works via `/generate-changelog` command or `bash changelog.sh` (or `python changelog.py`)**
- [x] **Fetches commits since the last git tag** (or initial commit if no tags exist)
- [x] **Auto-categorizes into**: `Added` / `Fixed` / `Changed` / `Removed`
- [x] **Outputs a properly formatted `CHANGELOG.md`**
- [x] **Tested on a real GitHub repo**: Sample output included in [`skills/changelog-generator/CHANGELOG.sample.md`](skills/changelog-generator/CHANGELOG.sample.md)
- [x] **README with setup instructions in 3 steps or fewer**: Documented in [`skills/changelog-generator/README.md`](skills/changelog-generator/README.md)

---

## Deliverables in This PR

- `skills/changelog-generator/SKILL.md`: Native Claude Code skill definition.
- `skills/changelog-generator/changelog.py`: Cross-platform Python implementation.
- `skills/changelog-generator/changelog.sh`: Zero-dependency pure Bash script.
- `skills/changelog-generator/README.md`: 3-step setup guide and CLI options.
- `skills/changelog-generator/CHANGELOG.sample.md`: Real output generated from repo git history.
- `tests/test_changelog.py`: Automated test suite for categorization and formatting.
- `README.md`: Root repository README updated with skill reference and bounty status.

---

## Quick Setup (3 Steps or Fewer)

1. **Copy to Claude skills**:
   ```bash
   cp -r skills/changelog-generator/ ~/.claude/skills/
   ```
2. **Make executable**:
   ```bash
   chmod +x skills/changelog-generator/changelog.sh
   ```
3. **Run**:
   ```bash
   python3 skills/changelog-generator/changelog.py -o CHANGELOG.md
   # or
   bash skills/changelog-generator/changelog.sh -o CHANGELOG.md
   ```

---

## Verification Test Results

Command: `python -m unittest discover -s tests -p "test_changelog.py" -v`

```text
test_added_category (test_changelog.TestCommitCategorization.test_added_category) ... ok
test_changed_category (test_changelog.TestCommitCategorization.test_changed_category) ... ok
test_fixed_category (test_changelog.TestCommitCategorization.test_fixed_category) ... ok
test_removed_category (test_changelog.TestCommitCategorization.test_removed_category) ... ok
test_markdown_sections_and_ordering (test_changelog.TestMarkdownGeneration.test_markdown_sections_and_ordering) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.001s

OK
```

---

Closes #1
