# Real repository example

`CHANGELOG.md` is generated from the public repository that hosts the bounty:
<https://github.com/claude-builders-bounty/claude-builders-bounty>.

The checked revision is `1aeae2adc82d33f971fd7731644348dcdd24b5a6`.
This repository had two commits and no tags when tested, so the output includes
all history. Tagged history, merge behavior, and revision ranges are separately
covered by the offline integration tests.

To reproduce from the package directory:

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git /tmp/bounty-changelog-example
bash changelog.sh --repo /tmp/bounty-changelog-example --until 1aeae2adc82d33f971fd7731644348dcdd24b5a6 --output -
```

Choose an unused clone destination. The generator itself never accesses the network.
