# Sample outputs

Unedited output of `claude-review` run against two real, public GitHub pull
requests (model `claude-opus-4-8`, run 2026-07-01). Each file starts with an
HTML comment recording the exact PR URL, command, and token usage.

| Sample | PR | Confidence | Notable finding |
|---|---|---|---|
| [expressjs-express-5555.md](./expressjs-express-5555.md) | [expressjs/express#5555](https://github.com/expressjs/express/pull/5555) | High | Flagged `String(url)` coercion changing behavior for falsy inputs |
| [pallets-flask-5928.md](./pallets-flask-5928.md) | [pallets/flask#5928](https://github.com/pallets/flask/pull/5928) | Medium | Caught a possible `NameError` on the `sys` import, `KeyboardInterrupt` suppression, and the `ExceptionGroup` breaking change |
