# Generate Changelog Proof Map

This file connects the bounty requirements to the exact verification artifacts in the submission.

## Claimed Deliverables

- `changelog.sh`
- `generate-changelog/SKILL.md`
- `generate-changelog/README.md`
- `generate-changelog/changelog.sh`
- `generate-changelog/scripts/generate_changelog.py`
- `generate-changelog/samples/CHANGELOG.sample.md`
- `generate-changelog/scripts/verify_sample.py`
- `generate-changelog/scripts/verify_project.py`

## Verification Commands

### Sample output check

```bash
python generate-changelog/scripts/verify_sample.py
```

Confirms:

- bundled sample title exists
- bundled source note exists
- bundled changelog section headings exist

Expected success output:

```text
Sample changelog verification passed.
Checked 5 required snippets and section headings.
```

### End-to-end project check

```bash
python generate-changelog/scripts/verify_project.py
```

Confirms:

- generator help output is available
- bundled sample verification passes

Expected success output:

```text
Project verification passed.
Checked generator help output and bundled sample verification.
```

### Generator dry run

```bash
generate-changelog/scripts/generate_changelog.py --repo psf/requests --dry-run --max-pages 2
```

Confirms:

- remote GitHub API mode works
- the output can be generated from a real repository
- the resulting sample was written into `samples/CHANGELOG.sample.md`

Expected sample artifact:

- `generate-changelog/samples/CHANGELOG.sample.md`
