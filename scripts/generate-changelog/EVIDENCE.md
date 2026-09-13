# Verification evidence

Checked on 2026-09-13 in a Linux environment using Python 3.12.14, Git 2.51.1,
and GNU Bash 5.2.21. Other operating systems and Python versions were not run.

## Observed checks

| Check | Observed result |
| --- | --- |
| `python3 -m unittest -v test_changelog` | 37 tests passed; recorded full run took 1.268 seconds |
| `bash -n changelog.sh` | Exit 0 |
| `python3 -m py_compile changelog.py test_changelog.py` | Exit 0 |
| `bash changelog.sh --help` | Exit 0; documented options displayed |
| Generate from the real public bounty repository | Exit 0; two commits included |
| Read-only check of the example source repository afterward | Clean worktree; no tags |

The unit/integration checks run entirely offline. They create disposable Git
repositories and remove only those fixtures. The shallow-clone test clones its
own local fixture through a `file://` URL; it does not contact a remote.

No separate Gauntlet tool was available in this session. The verification above
was performed directly; it is not an independent security audit or a claim that
all possible inputs and filesystems are supported.

## Acceptance mapping

| Listing requirement, paraphrased | Candidate implementation / evidence |
| --- | --- |
| Bash or skill entry point | `bash changelog.sh` |
| Changes after the preceding tag | Reachable-tag selection, exclusive base, pinned end; integration tests |
| Four change categories | Added, Fixed, Changed, Removed; subject classification tests |
| Markdown output | `CHANGELOG.md` with escaped subjects and commit IDs |
| Real GitHub repository demonstration | `examples/CHANGELOG.md` and reproduction details |
| Short setup | Three numbered setup steps in `README.md` |

The listing is at
<https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1>.
These are implementation checks, not sponsor acceptance.

## Real-repository source

- Repository: <https://github.com/claude-builders-bounty/claude-builders-bounty>
- Pinned commit: `1aeae2adc82d33f971fd7731644348dcdd24b5a6`
- Initial commit: `a80a580e3419` (abbreviated)
- Reachable history: two commits; no tags in the checkout
- Result: one Added entry, one Changed entry, and empty Fixed/Removed sections

Generation command used (package directory as the working directory):

```bash
bash changelog.sh \
  --repo /workspace/scratch/8097997ca87f/bounty-reference \
  --until 1aeae2adc82d33f971fd7731644348dcdd24b5a6 \
  --output /workspace/scratch/8097997ca87f/changelog-bounty/examples/CHANGELOG.md
```

Output was written outside the source repository; no changes were pushed.

## Review notes

The local review checked argument separation, validated object IDs, branch/tag
name collisions, escaped Markdown, lossless Unicode subjects, deterministic
ordering, merge handling, and failure cleanup. It prompted a correction to path
handling so a repository name ending in a space is preserved; a regression test
covers that case. Output ordering is explicitly described as topological rather
than promising strict timestamp order across branches.

Existing changelogs are protected by default. `--force` replaces, not appends;
this limitation is documented. The real repository had no tags, so tag behavior
was verified using genuine Git repositories built by the tests.
