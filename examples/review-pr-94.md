# Sample review — PR #94 (ubiquity/uusd.ubq.fi)

Command:
```bash
claude-review --pr https://github.com/ubiquity/uusd.ubq.fi/pull/94
```

Output:

## Review of PR #94

### Summary
Reworks the token selector cache in `simplified-exchange-component.ts` to be keyed by token contract address (not symbol) and stops balance refreshes from wiping entries that are still owned. The amount label computation is now re-run after the selected token and the token options are restored so the label always matches the active selection.

### Risks
- Changing the cache key from symbol to address changes every `cache.get`/`cache.has` call site; if any cached value was previously indexed by symbol (for example a legacy path that still reads `tokenOptions` keys by symbol), it will silently miss and create a duplicate entry on the next refresh.
- The refresh path now mutates the existing cache entry instead of replacing the whole map; if an exception is thrown between "read existing entries" and "write merged result", the UI can momentarily show a stale snapshot rather than the last known-good state.
- Migrating persisted cache (if any is stored in browser storage) from symbol-keyed to address-keyed values is not covered, so pre-existing sessions may show duplicated token rows once after upgrade.

### Improvement suggestions
- **Cache key** — centralize the address-keyed lookup in one helper (e.g. `getCachedTokenByAddress`) instead of touching every call site, and add a comment documenting why symbol is unsafe (`simplified-exchange-component.ts`, near the cache definition).
- **Atomic merge** — wrap the "fetch balances → merge into existing entries" path so a failure mid-merge does not drop existing holdings; snapshot the previous cache and restore on error.
- **Migration** — on first load, detect symbol-keyed entries and re-index them by address so upgraded sessions do not lose or duplicate rows.

### Confidence
**Medium** — the logic is self-contained and the direction is sound, but behavior depends on runtime interaction between the refresh flow and the persisted token options, which is not fully visible in this diff.