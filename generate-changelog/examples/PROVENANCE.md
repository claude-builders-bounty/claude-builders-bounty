# Sample output provenance

`sample-changelog.md` in this folder is unedited output of `changelog.sh`,
produced on **2026-10-14** by running:

```bash
git clone https://github.com/sindresorhus/query-string.git
cd query-string   # HEAD at 7fd813338963583472586f228a74dcbfb067e785 (v9.5.1)
bash changelog.sh --all
```

It contains one section per release tag in that repository (91 sections,
v9.5.1 back through its earliest tags), categorized from the project's real
commit messages — no entries were written or edited by hand.

A single-release regeneration from the same clone
(`--from v9.5.0 --to v9.5.1 --version v9.5.1`) produces correct compare
links (`compare/v9.5.0...v9.5.1`); that output is kept with the submission's
local proof files.

The tool was additionally exercised on a synthetic test repository with a
scripted history (Conventional Commits, messy plain-English subjects, a
breaking change, a merge commit, three tags) covering the default,
`--version`, `--all`, insert-into-existing-file, duplicate-version-refusal,
empty-range, and no-tags paths.
