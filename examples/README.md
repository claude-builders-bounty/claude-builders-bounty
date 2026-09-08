# Public repository example

`click-CHANGELOG.md` was generated from [pallets/click](https://github.com/pallets/click) at commit [`6aabf099bfdd4c1e75fe8d0e0d4241372b988ab1`](https://github.com/pallets/click/commit/6aabf099bfdd4c1e75fe8d0e0d4241372b988ab1). Git selected tag `8.5.0` as the nearest reachable tag.

Reproduce with a full clone (in the generator directory):

```bash
git clone https://github.com/pallets/click.git /tmp/click-changelog-example
git -C /tmp/click-changelog-example checkout 6aabf099bfdd4c1e75fe8d0e0d4241372b988ab1
bash changelog.sh --repo /tmp/click-changelog-example --output examples/click-CHANGELOG.md
```

Only Git history was read; no Click code was executed. This is generated development history, not an official Click release announcement. The sample intentionally retains both a change and its subsequent revert: deciding whether to omit them is part of reviewing the draft. Commit subjects come from the Click contributors; the upstream license is included as `CLICK_LICENSE.txt`.
