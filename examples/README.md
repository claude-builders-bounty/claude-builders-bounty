# Real-repository example

Source: https://github.com/pallets/itsdangerous

Verified on 2026-10-22 with Git and Python on Windows. Captured HEAD: `672971d66a2ef9f85151e53283113f33d642dabd`. Automatically selected reachable tag: `2.1.x`.

Reproduce from the generator directory (with an unused examples output path):

```bash
git clone https://github.com/pallets/itsdangerous.git ../itsdangerous-example
git -C ../itsdangerous-example checkout 672971d66a2ef9f85151e53283113f33d642dabd
bash changelog.sh --repo ../itsdangerous-example --output examples/reproduced.md
```

The included CHANGELOG.md is the actual generated output. The source checkout had complete history and tags; no source files were executed. Generic maintenance subjects map to Changed, as documented. This example demonstrates a real project's history, not endorsement by its maintainers.
