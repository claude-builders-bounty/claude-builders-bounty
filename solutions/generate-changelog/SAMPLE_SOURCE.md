# Real-repository verification

Source: https://github.com/pallets/itsdangerous

Verified on 2026-09-08 using Windows, Python 3.11, Git 2.21 and Git Bash.

- HEAD: `672971d66a2ef9f85151e53283113f33d642dabd`
- Automatically selected nearest reachable tag: `2.1.x`
- Base commit: `3ddb1ce418712d02f674a171b3f13ab20f6839a7`
- Commits after the boundary: 60
- Sample SHA-256: `8eb08600f05058885c0e30b9dacfb8477ad12e4d27b8afa3603a607ae5820727`

The repository uses a maintenance tag (`2.1.x`). This is the actual result of Git's nearest-reachable-tag selection, not an inferred semantic version. Use `--since` for another release convention.

Reproduce from this tool directory:

```bash
git clone https://github.com/pallets/itsdangerous.git /tmp/itsdangerous-sample
git -C /tmp/itsdangerous-sample checkout 672971d66a2ef9f85151e53283113f33d642dabd
bash changelog.sh --repo /tmp/itsdangerous-sample --since 3ddb1ce418712d02f674a171b3f13ab20f6839a7 --stdout
```

The explicit commit makes the range reproducible if tag refs later change. It changes only the displayed boundary label; commit entries remain the same. No source project code needs to execute.

Independent validation compared every `git rev-list 3ddb1ce418712d02f674a171b3f13ab20f6839a7..672971d66a2ef9f85151e53283113f33d642dabd` commit with the generated links: all 60 appear exactly once and the boundary commit is excluded. The Bash wrapper's `--check` also returned 0 against the saved sample. The regression suite passed 19 tests; see `VALIDATION.txt`.

The full upstream source is not included in the delivery archive. This sample reproduces commit subjects and commit links from the public repository as a generated changelog example.
