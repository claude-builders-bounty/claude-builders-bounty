# Advanced CHANGELOG Generator Usage

## Use Case 1: Multiple Repositories

Generate a combined CHANGELOG for multiple repos:

```bash
# Create combined changelog
for repo in repo1 repo2 repo3; do
  bash changelog.sh --repo /path/to/$repo --output CHANGELOG-$repo.md
done

# Merge
cat CHANGELOG-*.md > COMBINED-CHANGELOG.md
```

## Use Case 2: Semantic Versioning

Only include changes since last major version:

```bash
# Generate for v2.x
bash changelog.sh --from-tag v2.0.0 --output CHANGELOG-v2.md
```

## Use Case 3: CI/CD Integration

Add to GitHub Actions:

```yaml
name: Update CHANGELOG
on:
  push:
    tags:
      - 'v*'

jobs:
  changelog:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Generate CHANGELOG
        run: |
          bash changelog.sh --output CHANGELOG.md
      - name: Commit CHANGELOG
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add CHANGELOG.md
          git commit -m "docs: update CHANGELOG"
          git push
```

## Use Case 4: Slack Integration

Send changelog to Slack:

```bash
# Generate and send
bash changelog.sh --output /tmp/changelog.md
curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"$(cat /tmp/changelog.md)\"}" \
  $SLACK_WEBHOOK_URL
```

## Use Case 5: Multi-language Output

Generate in different languages:

```bash
# Chinese
export LANG=zh_CN.UTF-8
bash changelog.sh --output CHANGELOG-zh.md

# Japanese
export LANG=ja_JP.UTF-8
bash changelog.sh --output CHANGELOG-ja.md
```

## Customization

### Change commit categories

Edit `changelog.sh`:

```bash
CATEGORIES=(
  "feat:Added"
  "fix:Fixed"
  "docs:Documentation"
  "style:Styling"
  "refactor:Refactored"
  "test:Tests"
  "chore:Chores"
)
```

### Change output format

Edit `changelog.sh`:

```bash
# Markdown (default)
FORMAT="markdown"

# HTML
FORMAT="html"

# JSON
FORMAT="json"
```
