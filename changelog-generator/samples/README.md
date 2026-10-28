# Real GitHub history sample

The adjacent [CHANGELOG.markupsafe.md](CHANGELOG.markupsafe.md) was generated from
[pallets/markupsafe](https://github.com/pallets/markupsafe), with no source scripts
executed and no invented commits or tags.

- HEAD: `4e111271b1494995708a9e878a10829b5e10c7ba`
- Nearest reachable tag: `3.0.4`
- Tagged commit: `ece26078ec168ebac69f02877238e68d4b376c91`
- Range: 22 commits reachable from HEAD but not from the tagged commit.

The range includes earlier main-branch changes that were not ancestors of the
tag on the stable branch. It is Git reachability, not a date filter. Empty Added
and Fixed sections reflect these actual subjects; synthetic tests cover all four
categories separately. Reverts stay Changed because they may restore behavior.

To reproduce, from this generator checkout:

```sh
git clone --no-checkout https://github.com/pallets/markupsafe.git /tmp/markupsafe-sample
git -C /tmp/markupsafe-sample checkout --detach 4e111271b1494995708a9e878a10829b5e10c7ba
python3 tests/check_sample.py /tmp/markupsafe-sample
```

The check invokes `bash changelog.sh`, compares the exact committed sample bytes
and independently checks every range commit ID. It writes only a temporary
output file; the generator does not modify sample history or project source.
