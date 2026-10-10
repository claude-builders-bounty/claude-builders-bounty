# Structured changelog generator

Dependency-free Python tool with a Bash entry point for issue #1. Groups commits since the last reachable tag into Added, Fixed, Changed and Removed, includes commit IDs, marks breaking conventional commits, and escapes untrusted subjects. Existing files are preserved unless `--force` is used.

## Setup

1. Install Git and Python 3.9+.
2. Copy this directory into your tools directory.
3. From the target repository run `bash /path/to/changelog.sh` (Windows: `python /path/to/generate_changelog.py`).

Optional arguments: `--repo PATH`, `--since TAG`, `--version VERSION`, `--output PATH`, `--stdout`, `--force`. No tag means all available non-merge history. Shallow clones are explicitly identified in the output; use a complete clone for a full release history. Categorization is deterministic and should be reviewed before a release.

`SAMPLE_CHANGELOG.md` was generated from the real psf/requests repository; its pinned revision is recorded in `validation.json`. Run `python -m unittest -v test_generator.py` here to reproduce the focused regression checks. The tool does not execute commit contents, send data, or call paid APIs.

Original AI-assisted contribution by HHR Nexus on behalf of its owner. MIT license, as provided by the parent repository.
