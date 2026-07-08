# Testing

## Local Test

```bash
python3 submissions/issue-1-generate-changelog-skill/tests.py
```

Result:

```text
tests_ok=true
```

## Real GitHub Repo Sample

Generated with:

```bash
git clone --depth 200 --tags https://github.com/pallets/markupsafe.git /tmp/markupsafe-changelog-sample
bash submissions/issue-1-generate-changelog-skill/changelog.sh \
  --repo /tmp/markupsafe-changelog-sample \
  --output /absolute/path/to/samples/markupsafe-changelog.md
```

Included output:

- `samples/markupsafe-changelog.md`
