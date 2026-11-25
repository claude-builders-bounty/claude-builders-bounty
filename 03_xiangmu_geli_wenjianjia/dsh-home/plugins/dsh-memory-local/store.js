// 本地向量记忆存储：JSONL + bge-m3 嵌入 + 余弦检索
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const enc = (vec) => Buffer.from(new Float32Array(vec).buffer).toString('base64');
const dec = (s) => { const b = Buffer.from(s, 'base64'); return new Float32Array(b.buffer, b.byteOffset, b.byteLength / 4); };
const norm = (s) => String(s ?? '').replace(/\s+/g, ' ').trim();

export function hashText(text) {
  return createHash('sha256').update(norm(text).toLowerCase()).digest('hex').slice(0, 16);
}

function cosine(a, b) {
  let dot = 0, na = 0, nb = 0;
  const n = Math.min(a.length, b.length);
  for (let i = 0; i < n; i++) { const x = a[i], y = b[i]; dot += x * y; na += x * x; nb += y * y; }
  return na && nb ? dot / Math.sqrt(na * nb) : 0;
}

export function createMemoryStore(options = {}) {
  const dir = options.dir;
  const file = join(dir, 'memories.jsonl');
  const url = (options.url || 'http://127.0.0.1:11434').replace(/\/$/, '');
  const model = options.model || 'bge-m3';
  const maxEntries = options.maxEntries || 5000;
  let entries = null;
  let hashes = new Set();

  function ensure() {
    if (entries) return;
    entries = [];
    hashes = new Set();
    try {
      if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
      if (!existsSync(file)) return;
      for (const line of readFileSync(file, 'utf8').split('\n')) {
        if (!line.trim()) continue;
        try {
          const e = JSON.parse(line);
          if (!e || typeof e.text !== 'string' || typeof e.vec !== 'string') continue;
          entries.push({ ...e, v: dec(e.vec) });
          hashes.add(e.hash);
        } catch {}
      }
    } catch {}
  }

  function persist() {
    try {
      ensure();
      if (entries.length > maxEntries) entries = entries.slice(entries.length - maxEntries);
      const body = entries.map((e) => JSON.stringify({ id: e.id, ts: e.ts, cwd: e.cwd, session: e.session, kind: e.kind, text: e.text, hash: e.hash, vec: e.vec })).join('\n') + '\n';
      const tmp = file + '.tmp';
      writeFileSync(tmp, body, 'utf8');
      renameSync(tmp, file);
    } catch {}
  }

  async function embed(input) {
    const res = await fetch(url + '/api/embed', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ model, input: Array.isArray(input) ? input : [input] }),
      signal: AbortSignal.timeout(options.timeoutMs || 20000),
    });
    if (!res.ok) throw new Error('ollama embed HTTP ' + res.status);
    const json = await res.json();
    const list = json.embeddings || (json.embedding ? [json.embedding] : []);
    if (!list.length || !list[0]?.length) throw new Error('ollama embed returned no vector');
    return list;
  }

  async function add({ text, cwd, session, kind = 'turn', ts = Date.now() }) {
    const clean = norm(text);
    if (clean.length < (options.minChars || 16)) return null;
    ensure();
    const hash = hashText(clean);
    if (hashes.has(hash)) return null;
    const [vec] = await embed(clean);
    const entry = { id: hash, ts, cwd: cwd || '', session: session || '', kind, text: clean.slice(0, options.maxTextChars || 2000), hash, vec: enc(vec), v: Float32Array.from(vec) };
    entries.push(entry);
    hashes.add(hash);
    persist();
    return entry.id;
  }

  async function addExplicit(text, extra = {}) {
    return add({ text, kind: 'explicit', ...extra });
  }

  async function search(query, k = 5, minScore = 0.35) {
    ensure();
    const clean = norm(query);
    if (!clean) return [];
    if (!entries.length) return [];
    let qv;
    try { [qv] = await embed(clean); } catch { return []; }
    const q = Float32Array.from(qv);
    return entries
      .map((e) => ({ text: e.text, ts: e.ts, cwd: e.cwd, kind: e.kind, score: cosine(q, e.v) }))
      .filter((r) => r.score >= minScore)
      .sort((a, b) => b.score - a.score)
      .slice(0, k);
  }

  function stats() {
    ensure();
    return { count: entries.length, dir, model, url, file };
  }

  return { add, addExplicit, search, stats, ensure, embed };
}
