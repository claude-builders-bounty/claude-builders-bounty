---
name: scope-recall-vector-migration
description: Run Scope Recall vector migration, handle writer lease.
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, windows]
metadata:
  hermes:
    tags: [scope-recall, vector-migration, chromadb, embeddings, sqlite]
    related_skills: [memory-local, configure-hermes-memory-provider, hermes-full-health-check]
---

# Scope Recall Vector Migration

Execute Scope Recall vector generation migration (`migrate.vector_generation.py --apply`, `--activate-existing-ready`) with proper writer lease handling, SQLite schema verification, and ChromaDB backend sync.

## When to Use

- After Scope Recall schema upgrade or config change
- When ChromaDB collections are empty but SQLite has data
- After changing embedder (e.g., Gemini → local, or model swap)
- When `hermes-full-health-check` reports "ChromaDB empty" or "Vector migration needed"
- Scheduled maintenance (run after daily compression)

## Prerequisites

- Scope Recall plugin installed at `~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/scope_recall/`
- Hermes home at `~/.hermes/` (or `$HERMES_HOME`)
- Embedder configured: `SCOPE_RECALL_GEMINI_EMBEDDING_API_KEY` in `.env` OR local embedder
- Ollama accessible at `http://172.24.160.1:11434` (for bge-m3 if used)
- **Gateway must be STOPPED** for `--activate-existing-ready` (writer lease conflict)

## How to Run

```bash
# 1. Stop gateway to release writer lease
systemctl --user stop hermes-gateway hermes-gateway-empress

# 2. Run migration --apply (builds shadow generation)
SCOPE_RECALL_GEMINI_EMBEDDING_API_KEY=ollama \
  /home/user01/.hermes/hermes-agent/venv/bin/python \
  /home/user01/.hermes/hermes-agent/venv/lib/python3.11/site-packages/scope_recall/scripts/migrate.vector_generation.py \
  --hermes-home /home/user01/.hermes --apply

# 3. Activate the ready generation (requires gateway stopped)
SCOPE_RECALL_GEMINI_EMBEDDING_API_KEY=ollama \
  /home/user01/.hermes/hermes-agent/venv/bin/python \
  /home/user01/.hermes/hermes-agent/venv/lib/python3.11/site-packages/scope_recall/scripts/migrate.vector_generation.py \
  --hermes-home /home/user01/.hermes --activate-existing-ready --generation-id <GEN_ID_FROM_STEP_2>

# 4. Restart gateway
systemctl --user start hermes-gateway-empress
```

## Quick Reference

| Task | Command |
|------|---------|
| Stop gateway | `systemctl --user stop hermes-gateway hermes-gateway-empress` |
| Build vectors (--apply) | `python migrate.vector_generation.py --hermes-home ~/.hermes --apply` |
| Activate ready gen | `python migrate.vector_generation.py --hermes-home ~/.hermes --activate-existing-ready --generation-id <ID>` |
| Check status | `python migrate.vector_generation.py --hermes-home ~/.hermes --status` |
| Restart gateway | `systemctl --user start hermes-gateway-empress` |

## Procedure

### 1. Verify Preconditions
```bash
# Check SQLite DB exists with tables
sqlite3 ~/.hermes/memory/scope_recall.db ".tables"
# Should show: fact memory ops preference project user

# Check ChromaDB state
python3 -c "import chromadb; c=chromadb.PersistentClient('/home/user01/.hermes/chroma'); print(f'Collections: {len(c.list_collections())}')"

# Check embedder config
grep SCOPE_RECALL ~/.hermes/.env
```

**Completion criterion:** SQLite has 6 tables, embedder key present in .env.

### 2. Stop Gateway Services
```bash
systemctl --user stop hermes-gateway hermes-gateway-empress
systemctl --user is-active hermes-gateway hermes-gateway-empress
# Both should show "inactive"
```
**Completion criterion:** Both gateway services inactive.

### 3. Run Vector Generation Build (--apply)
```bash
cd /home/user01/.hermes/hermes-agent/venv/lib/python3.11/site-packages/scope_recall/scripts
SCOPE_RECALL_GEMINI_EMBEDDING_API_KEY=ollama \
  python migrate.vector_generation.py --hermes-home /home/user01/.hermes --apply 2>&1
```
**Completion criterion:** Output shows `"ok": true`, `"rebuilt": true`, `"rows_built": N`, `"status": "ready"`, and a `generation_id` like `gen-20260907T214008Z-bge-m3-5e89cb65`.

### 4. Activate the Ready Generation
```bash
SCOPE_RECALL_GEMINI_EMBEDDING_API_KEY=ollama \
  python migrate.vector_generation.py --hermes-home /home/user01/.hermes --activate-existing-ready --generation-id <GEN_ID_FROM_STEP_3> 2>&1
```
**Completion criterion:** Output shows `"ok": true`, `"activated": true` (or similar success). If `TruthWriterBusyError`, gateway still running → repeat step 2.

### 5. Verify Vector Store Populated
```bash
python3 -c "
import chromadb
c = chromadb.PersistentClient('/home/user01/.hermes/chroma')
cols = c.list_collections()
print(f'Collections: {len(cols)}')
for col in cols:
    print(f'  {col.name}: {col.count()} docs')
"
```
**Completion criterion:** At least one collection with >0 documents.

### 6. Restart Gateway
```bash
systemctl --user start hermes-gateway-empress
journalctl --user -u hermes-gateway-empress -f -n 20
# Wait for "Connected in websocket mode (feishu)"
```

## Pitfalls

- **TruthWriterBusyError**: Gateway holds SQLite write lease. **Must stop BOTH gateway services** before activation.
- **别把两种「写租约」搞反 —— 一个要治，一个别动**：
  - `TruthWriterBusyError`（抛在 `--activate-existing-ready` 时）= 你**正在做写操作**、被别人持着租约 → 必须停网关。
  - `Scope Recall truth writer lease is held by another process; continuing in read-only recall mode`
    （普通进程启动时打的一条 WARNING）= **设计如此、已自动降级只读**，召回照常工作。
    **千万不要为了让这条日志消失而停网关**，也不要把它当成实例冲突上报。
    验证它真无害只需看 `memory.sqlite3` 及其 `-wal` 的 mtime 是不是新的（写入没停），
    以及 `cat "$HERMES_HOME/scope-recall/.truth-writer.lease.info"` 是否为 `{"role": "provider"}`。
- **Insecure HTTP warning**: Ollama at HTTP endpoint triggers warning; harmless for local dev.
- **Generation ID format**: Must match exactly (e.g., `gen-20260907T214008Z-bge-m3-5e89cb65`).
- **Embedder mismatch**: If embedder changed, must rebuild all vectors (--apply does this).
- **ChromaDB path**: Uses `~/.hermes/chroma/` by default; verify in Scope Recall config.

## Verification

```bash
# 1. ChromaDB has collections with data
python3 -c "import chromadb; c=chromadb.PersistentClient('/home/user01/.hermes/chroma'); assert len(c.list_collections()) > 0 and c.list_collections()[0].count() > 0"

# 2. Gateway starts cleanly
systemctl --user is-active hermes-gateway-empress
# → active

# 3. Memory recall works in next session
# (Test by asking agent to recall a known fact)
```

---

*Skill distilled from sessions 20260908_042140_65b6a3aa, cron_ead55c70d699_20260831_180001 (2+ occurrences: vector migration --apply, writer lease conflict, activation). Pattern threshold met via recurring maintenance need. **Sep 22, 2026**: added dual profile sync cross-reference; verified two-step --apply then --activate-existing-ready process with writer lease handling.*