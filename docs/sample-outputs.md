# Sample PR Review Outputs

These examples were generated with the local CLI against real public GitHub
pull requests.

## Example 1

Command:

```bash
claude-review --pr https://github.com/pypa/sampleproject/pull/214
```

Output:

```markdown
# PR Review

Source: https://github.com/pypa/sampleproject/pull/214

## Summary of Changes

- This PR changes 1 file with 2 additions and 2 deletions.
- The touched files are mostly configuration, generated, or non-source assets.
- Highest-review files: `.github/workflows/test.yml`.

## Identified Risks

- Build, dependency, or workflow configuration changed in `.github/workflows/test.yml`.

## Improvement Suggestions

- Run the full CI matrix and check lockfile or workflow changes for supply-chain impact.

## Confidence Score: Medium

Reviewed 1 file, 2 additions, and 2 deletions. Confidence is based on diff size, test coverage signals, and sensitive-area heuristics.
```

## Example 2

Command:

```bash
claude-review --pr https://github.com/psf/requests/pull/7460
```

Output:

```markdown
# PR Review

Source: https://github.com/psf/requests/pull/7460

## Summary of Changes

- This PR changes 1 file with 1 addition and 1 deletion.
- The main touched areas are 1 source file.
- Highest-review files: `src/requests/sessions.py`.

## Identified Risks

- Production code changed without an accompanying test file.

## Improvement Suggestions

- Add or update tests that cover the changed behavior before merge.

## Confidence Score: Medium

Reviewed 1 file, 1 addition, and 1 deletion. Confidence is based on diff size, test coverage signals, and sensitive-area heuristics.
```

The generated files are also available as:

- [sample-output-pypa-sampleproject-214.md](sample-output-pypa-sampleproject-214.md)
- [sample-output-psf-requests-7460.md](sample-output-psf-requests-7460.md)

