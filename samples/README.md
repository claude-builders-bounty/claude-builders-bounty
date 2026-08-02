# Real-PR smoke tests

These two captured outputs were produced locally on 2026-08-01 with the
dependency-free fallback. They use public, real GitHub pull requests and are
included so the acceptance requirement is reproducible even on a machine
without the `claude` executable. With Claude Code installed, omit `--offline`
to run the same inputs through the model-backed path.

```text
python claude_review.py --pr https://github.com/masterazul/keyrot/pull/1 --offline
python claude_review.py --pr https://github.com/FLucasF/task-manager/pull/24 --offline
```

- [masterazul/keyrot#1](https://github.com/masterazul/keyrot/pull/1): dependency update, 2 files, +20/-3.
- [FLucasF/task-manager#24](https://github.com/FLucasF/task-manager/pull/24): test coverage change, 2 files, +21/-2.
