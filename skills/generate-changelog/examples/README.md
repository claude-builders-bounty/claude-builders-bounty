# Real GitHub repository test: pallets/click

Source: https://github.com/pallets/click (public; source code was not executed).

| Field | Recorded value |
| --- | --- |
| HEAD | `8abb77a8432e03ed14a95f972b44f905279415a7` |
| Nearest reachable tag | `8.5.1` |
| Tag commit | `cf19179e8e2fd54c601378cec9e0d21bb12b6fb1` |
| Commits in `8.5.1..HEAD` | 19 |
| Output entries | 19 (6 Added, 13 Changed) |
| Checkout | Full Git history; shallow clone unshallowed before final test |

Reproduce from the bounty repository root (the `click-example` directory must
not already exist):

```bash
git clone https://github.com/pallets/click.git click-example
git -C click-example checkout --detach 8abb77a8432e03ed14a95f972b44f905279415a7
bash skills/generate-changelog/changelog.sh --repo click-example --stdout > click-CHANGELOG.md
diff -u skills/generate-changelog/examples/click-CHANGELOG.md click-CHANGELOG.md
```

The last command should produce no differences. This sample is actual output,
not a hand-written fixture. Fixed/Removed behavior is tested in the automated
Git integration suite; this particular upstream range contains neither type
under the documented prefix rules.
