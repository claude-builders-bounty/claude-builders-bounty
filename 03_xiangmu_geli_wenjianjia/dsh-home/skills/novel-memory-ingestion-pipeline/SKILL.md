---
name: novel-memory-ingestion-pipeline
description: Ingest novels into vector memory with entities & summaries.
version: 0.1.0
author: User (Hermes Agent)
license: MIT
platforms: [linux, windows]
metadata:
  hermes:
    tags: [memory, novel-processing, vector-ingestion, entity-extraction, hierarchical-summary]
    related_skills: [memory-local, cross-platform-text-processing, hermes-agent-skill-authoring]
---

# Novel Memory Ingestion Pipeline

Ingest multi-megabyte Chinese novels (GBK/UTF-8) into Hermes local vector memory (ChromaDB + bge-m3) with automatic chapter detection, entity/relation extraction, hierarchical summarization (chapter → volume → book), and three-layer query routing (vector → entity graph → summary skeleton).

## When to Use

- Ingest a large novel (100K+ words) for semantic search and structured recall
- Need zero-hallucination, chapter-cited answers about plot, characters, terms
- Process GBK-encoded Chinese novels from Windows paths via WSL2 read-only mounts
- Build a queryable knowledge base for roleplay, writing assistance, or research

Don't use for:
- Real-time chat memory (use `memory-local` hooks instead)
- Small documents (< 50KB) — direct vector add is simpler
- Non-text sources (PDF, EPUB — use `ocr-and-documents` first)

## Prerequisites

- WSL2 with `/mnt/c`, `/mnt/d` mounted read-only (`/etc/wsl.conf` with `ro,uid=1000,gid=1000`)
- Ollama running on Windows host at `172.24.160.1:11434` with `bge-m3` and `qwen2.5:7b` pulled
- ChromaDB server on `127.0.0.1:8000` (via `hermes-memory-provider-setup`)
- Python 3.10+ in `/home/user01/.hermes/python/.venv` with `chromadb`, `ollama`, `pyyaml`, `requests`
- Novel text file accessible at `/mnt/c/...` or `/mnt/d/...` (read-only)

## How to Run

```bash
# 1. Convert encoding if needed (GBK -> UTF-8)
iconv -f GBK -t UTF-8 "/mnt/c/Books/novel.txt" > "/home/user01/.hermes/python/data/novel/novel_utf8.txt"

# 2. Run full ingestion pipeline (dry-run first)
cd /home/user01/.hermes/python
python scripts/novel_ingest.py \
  --input "/home/user01/.hermes/python/data/novel/novel_utf8.txt" \
  --book-id "my_novel" \
  --stage scan --dry-run

# 3. Execute full pipeline (vector + entities + summaries)
python scripts/novel_ingest.py \
  --input "/home/user01/.hermes/python/data/novel/novel_utf8.txt" \
  --book-id "my_novel" \
  --stage all --apply

# 4. Query the ingested novel
python scripts/novel_query.py --book-id "my_novel" "主角在第几章突破金丹期"
```

## Quick Reference

| Task | Command |
|------|---------|
| Encoding convert | `iconv -f GBK -t UTF-8 input.txt > output.txt` |
| Scan novel structure | `python novel_ingest.py -i input.txt -b book_id --stage scan` |
| Full ingestion | `python novel_ingest.py -i input.txt -b book_id --stage all --apply` |
| Query (vector) | `python novel_query.py -b book_id "搜索关键词"` |
| Query (entity) | `python novel_query.py -b book_id --mode entity "角色名"` |
| Query (summary) | `python novel_query.py -b book_id --mode summary "剧情概括"` |

## Procedure

### 1. Scan & Validate Input (Stage: scan)

**Completion criterion**: `novel_analysis.json` produced with chapter index, encoding verified, char/token counts.

```python
# Steps:
# 1. Detect encoding (chardet), convert to UTF-8 if GBK/GB18030
# 2. Extract chapter markers: "第X章[.·]标题" / "Chapter X" regex
# 3. Build chapter index: [{title, byte_offset, char_count, est_tokens}, ...]
# 4. Identify volume/arc boundaries (every 50-100 chapters or explicit markers)
# 5. Output analysis JSON + stats (total chars, chapters, volumes)
```

### 2. Chunk & Vector Ingest (Stage: vector)

**Completion criterion**: ChromaDB collection `novel_{book_id}` populated with chunk embeddings + metadata.

```python
# Steps:
# 1. Chunk by paragraph with overlap (config: chunk_size=800, overlap=150 tokens)
# 2. Preserve chapter metadata on each chunk (chapter_idx, chapter_title, volume_idx)
# 3. Embed via Ollama bge-m3 (batch 32), upsert to ChromaDB
# 4. Verify: collection count == chunk count, sample query returns relevant chunks
```

### 3. Entity & Relation Extraction (Stage: entities)

**Completion criterion**: Scope Recall `project` target populated with entities/relations, chapter-cited.

```python
# Steps:
# 1. Batch chapters (5 per LLM call) → extractor LLM (qwen2.5:7b via Ollama)
# 2. Extract: character, location, organization, event, term, item
# 3. Extract relations: belongs_to, located_at, participated_in, knows, wields, causes
# 4. Deduplicate by canonical name + aliases; merge chapter citations
# 5. Store via scope_recall_store(target="project", memory_type="factual/entity/event")
```

### 4. Hierarchical Summarization (Stage: summaries)

**Completion criterion**: Three-layer summaries written to `data/novel/{book_id}/summaries/`.

```python
# Layer 1 - Chapter (parallel, 300 chars each):
#   Input: chapter text → Output: core events, char state changes, foreshadowing, structural role

# Layer 2 - Volume (sequential, 1500 chars each):
#   Input: N chapter summaries → Output: main arc, subplot convergence, conflict escalation, char arcs, new lore

# Layer 3 - Book (single, 5000 chars):
#   Input: all volume summaries → Output: overall structure, foreshadowing chains, char growth paths, worldbuilding reveal order, themes
```

### 5. Verification & Quality Gates (Stage: verify)

**Completion criterion**: All checks pass; query smoke test returns cited results.

```bash
# Checks:
# 1. ChromaDB collection exists, count > 0, sample query works
# 2. Scope Recall project has entities for book_id, probe returns results
# 3. Summary files exist at all three layers, non-empty, UTF-8
# 4. Cross-ref: entity chapter citations match actual chapter ranges
# 5. Smoke query: "主角名" returns vector chunks + entity card + summary reference
```

## Pitfalls

| Issue | Solution |
|-------|----------|
| GBK decode fails on rare chars | Use `GB18030` fallback; `errors='replace'` for unrecoverable bytes |
| Chapter regex misses variants | Support `第X章`, `第X章.`, `第X章·`, `Chapter X`, `卷X` patterns |
| Vector ingestion OOM on large novels | Batch embed (32), stream chunks from disk, don't hold full text in RAM |
| Entity extraction hallucinates | Strict prompt: "只输出原文出现的实体，每个必须引用章节号" + post-filter against chapter index |
| Scope Recall writer lease conflict | Stop Hermes gateway before bulk entity ingest; restart after |
| Query returns stale vector results | Rebuild ChromaDB index after ingestion; verify `hnsw_space: cosine` |

## Verification

```bash
# 1. Collection stats
python -c "
import chromadb
c = chromadb.HttpClient(host='127.0.0.1', port=8000)
col = c.get_collection('novel_my_novel')
print(f'Chunks: {col.count()}')
print(col.peek(3))
"

# 2. Entity probe
hermes skill run scope_recall_entity probe "主角名" --target project --project my_novel

# 3. Summary files exist
ls -la /home/user01/.hermes/python/data/novel/my_novel/summaries/

# 4. End-to-end query
python scripts/novel_query.py -b my_novel "主角的师父是谁"
# Expected: vector chunks (chapter cite) + entity card (relations) + volume summary ref
```

---

*Distilled from session 20260922_174422_43a45e32 (Sep 22, 2026) — novel ingestion for "整座大山都是我的猎场" (1072 chapters, 7.6MB GBK). Pattern threshold ≥3 met across: encoding conversion, chapter extraction, entity extraction, hierarchical summarization, three-layer routing.*