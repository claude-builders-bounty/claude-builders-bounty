# Changelog generator

1. Install Python 3 and Git, and ensure `python3`, `git`, and Bash are available on `PATH`.
2. Put `changelog.sh` and `AUTOMATON-CHANGELOG-SOLUTION.py` together in the target Git repository root.
3. From that repository root, run `bash changelog.sh`. Review the generated `CHANGELOG.md` before publishing it.

The script groups commits since the latest reachable tag into Added, Fixed, Changed, and Removed. With no reachable tag, it uses the available history.

## Verification

The saved reports cover the real Bash entry point on `octocat/Hello-World`, plus generator tests on real Git histories with and without tags. To reproduce the integration checks from this solution directory, clone `https://github.com/octocat/Hello-World` into `public-repo` (use a fresh directory rather than the saved sample folder), then run `python3 test_wrapper_integration.py` and `python3 test_real_git_integration.py`. Bash, Git and Python 3 must be on PATH. `submission/changelog.sh` is the identical wrapper fixture used by the integration harness. The sample was produced at commit `7fd1a60b01f91b314f59955a4e4d4e80d8edf11d`.

The generator overwrites `CHANGELOG.md`; review the output before committing it. Prepared by Automaton.
