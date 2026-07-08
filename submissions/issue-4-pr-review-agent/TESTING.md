# Testing

## Local Unit Test

```bash
python3 submissions/issue-4-pr-review-agent/tests.py
```

Result:

```text
tests_ok=true
```

## Real PR Samples

Generated with:

```bash
submissions/issue-4-pr-review-agent/claude-review \
  --pr https://github.com/psf/requests/pull/7561 \
  --output submissions/issue-4-pr-review-agent/samples/psf-requests-pr.md

submissions/issue-4-pr-review-agent/claude-review \
  --pr https://github.com/pallets/flask/pull/6013 \
  --output submissions/issue-4-pr-review-agent/samples/pallets-flask-pr.md
```

Included outputs:

- `samples/psf-requests-pr.md`
- `samples/pallets-flask-pr.md`
