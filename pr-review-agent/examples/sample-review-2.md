<!-- claude-review of pallets/click#3780 -->
<!-- https://github.com/pallets/click/pull/3780 · diff: 51 lines, 2 files -->

## Summary
Documents why `click.edit()` can return immediately with some editors (VS Code's
`code` launcher exits after spawning the real editor), adding a new FAQ section
with per-editor `EDITOR` flag workarounds and a warning box on the `edit()`
docstring pointing readers to it.

## Risks
- Docs-only change; no runtime risk to Click itself.
- The `(edit-wait)=` MyST target must resolve from the docstring `:ref:`; if the FAQ file isn't included in the same sphinx build scope as the API docs, the reference could render unresolved.
- Table content assumes flags stay stable across editor versions (`--wait`, `-w`) — low but nonzero maintenance surface.

## Suggestions
- Mention that `require_save=True` also means the returned value is `None` when the editor never wrote the temp file — the FAQ touches this but the docstring warning could state the observable symptom once more explicitly.
- Consider linking JetBrains/other common launchers in the table since the same launcher pattern applies broadly.
- Nit: "Setup your editor" → "Set up your editor" (verb form) in the FAQ body.

## Confidence
High — small, self-contained documentation improvement with correct root-cause explanation.
