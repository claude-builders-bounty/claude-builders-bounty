# Sample provenance

Source: https://github.com/claude-builders-bounty/claude-builders-bounty

Commit: `1aeae2adc82d33f971fd7731644348dcdd24b5a6`

Generated locally on September 21, 2026 from the public repository's full history with:

```sh
python generate-changelog/changelog.py --repo . --output generate-changelog/SAMPLE_CHANGELOG.md
```

This checkout has no reachable release tag, so the sample covers its entire history. The integration tests separately verify a tagged repository with post-tag commits in all four categories, an unrelated tag, a tag at HEAD, empty history, Unicode, Markdown escaping, and preservation of existing output.
