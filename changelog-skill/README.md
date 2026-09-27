# Changelog Skill — Opire $50 bounty entry (issue #1)

![bash](https://img.shields.io/badge/bash-changelog.sh-blue) ![tests](https://img.shields.io/badge/tests-10%2F10-green) ![deps](https://img.shields.io/badge/deps-none-lightgrey)

Bash-only skill (works on bash 3.2+): commits since last tag into structured
`CHANGELOG.md` (Breaking / Added / Fixed / Changed / Removed). No dependencies.

## Run (3 steps)

```bash
git clone <this-repo> && cd changelog-skill
bash changelog.sh --repo /path/to/project
cat CHANGELOG.md
```

| Flag | Default | Meaning |
|---|---|---|
| `--since TAG` | latest tag (auto) | Commits after TAG; unknown ref exits 1, writes nothing |
| `--version VER` | `Unreleased` | Release header + UTC date |
| `--out FILE` | `CHANGELOG.md` | Output file |
| `--repo DIR` | `.` | Repo to summarize |
| `--preview` | off | Print to stdout, write nothing |
| `--append` | off | Prepend to existing CHANGELOG, keep old entries |

## Proof
`samples/CHANGELOG.homelab-sample.md` — 6 real commits, short-SHAs.
`PROOF.md` + `tests/test_changelog.sh` (10/10) + CI workflow.
