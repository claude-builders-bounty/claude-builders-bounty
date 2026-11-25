// memory-local: 跨会话向量记忆（bge-m3 + 本地 JSONL）
// 写入：每个 turn 结束把「用户提问 + 助手回答」嵌入后落盘
// 召回：每个 turn 开始前按当前用户消息做余弦检索，注入系统提示
import { appendFileSync, mkdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { createMemoryStore } from './store.js';

export const name = 'memory-local';
export const inject = ['systemPrompt', 'tools'];

const SOURCE_KIND = 'memory-local';
const RECALL_ORDER = 8400;

function textOf(message) {
  if (!message) return '';
  let m = message;
  // assistant/message 事件把消息包在 .message 里
  if (m.message && typeof m.message === 'object' && (m.message.content || m.message.role)) m = m.message;
  const content = m.content ?? m.parts;
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    return content
      .filter((part) => part && part.type === 'text' && typeof part.text === 'string')
      .map((part) => String(part.text ?? ''))
      .join('\n')
      .trim();
  }
  if (typeof m.text === 'string') return m.text;
  return '';
}

function isInjected(message) {
  return message?.source?.kind === SOURCE_KIND;
}

// 运行时上下文、系统提醒、技能目录这些"伪用户消息"不进记忆
function isBoilerplate(text) {
  if (!text) return true;
  if (text.length > 4000) return true;
  if (/^<system-reminder>/.test(text)) return true;
  if (/^Time sampled/.test(text)) return true;
  if (/^Current runtime context\./.test(text)) return true;
  if (text.includes('Instructions from:') && text.includes('AGENTS.md')) return true;
  if (text.includes('<available_skills>')) return true;
  if (/^You are an AI agent powered by DeepSeek Harness/.test(text)) return true;
  return false;
}

const CUT_MARKERS = [
  'Current runtime context.',
  'Time sampled while preparing',
  '<system-reminder>',
  'Your parent agent id is',
  'Before you finish, send your result',
  'Additional instructions from:',
  '<available_skills>',
];

function cleanUserText(raw) {
  let t = String(raw || '').replace(/\r/g, '');
  for (const marker of CUT_MARKERS) {
    const i = t.indexOf(marker);
    if (i > 0) t = t.slice(0, i);
  }
  return t.trim();
}

function lastUserText(messages) {
  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i];
    if (!m || isInjected(m)) continue;
    if (m.role === 'user') {
      const text = textOf(m);
      if (text && !isBoilerplate(text)) return text;
    }
  }
  return '';
}

function stamp(ts) {
  try {
    return new Date(ts).toLocaleString('zh-CN', { hour12: false });
  } catch {
    return '';
  }
}

function blockFor(rows) {
  if (!rows.length) return '';
  const lines = rows.map((r) => {
    const head = `- [${stamp(r.ts)}] (${r.cwd || '未知目录'}) 相似度 ${r.score.toFixed(2)}`;
    const body = r.text.replace(/\n/g, '\n  ').slice(0, 600);
    return head + '\n  ' + body;
  });
  return [
    '<memory-recall>',
    '以下是从历史会话/长期记忆里召回的片段，按相似度排序。可能过时或不相关，只在确实有用时参考，不要对用户复述本段。',
    ...lines,
    '</memory-recall>',
  ].join('\n');
}

export function apply(ctx, config = {}) {
  const home = process.env.DSH_HOME || join(homedir(), '.dsh');
  const dir = config.dir || join(home, 'memory');
  const store = createMemoryStore({
    dir,
    url: config.ollamaUrl || process.env.OLLAMA_HOST || 'http://127.0.0.1:11434',
    model: config.embedModel || 'bge-m3',
    minScore: config.minScore ?? 0.45,
    minChars: config.minChars ?? 16,
    maxTextChars: config.maxTextChars ?? 2000,
    maxEntries: config.maxEntries ?? 5000,
  });
  const topK = config.k ?? 4;
  const debug = config.debug === true;

  function dbg(line) {
    if (!debug) return;
    try {
      mkdirSync(dir, { recursive: true });
      appendFileSync(join(dir, 'debug.log'), new Date().toISOString() + ' ' + line + '\n');
    } catch {}
  }

  let recallText = '';
  let pendingRecall = null;

  function scheduleRecall(query) {
    const q = String(query || '').trim();
    if (q.length < 6) return pendingRecall;
    pendingRecall = store
      .search(q, topK, config.minScore ?? 0.45)
      .then((rows) => { recallText = blockFor(rows); })
      .catch(() => { recallText = ''; });
    return pendingRecall;
  }

  // ---- 召回 ----
  ctx.on('agent/pre-step', async (payload, next) => {
    try {
      const messages = Array.isArray(payload?.messages) ? payload.messages : [];
      const query = lastUserText(messages);
      if (query) {
        await scheduleRecall(query);
        dbg('pre-step q=' + JSON.stringify(query.slice(0, 50)) + ' recall=' + recallText.length);
      } else if (pendingRecall) {
        await pendingRecall;
      }
    } catch {
      recallText = '';
    }
    return next();
  });

  ctx.systemPrompt.context({
    name: 'memory:recall',
    order: RECALL_ORDER,
    interpolate: false,
    text: () => recallText,
  });

  // ---- 写入：每个 turn 结束落盘 ----
  const pending = new Map();

  ctx.on('session/event', (session, event) => {
    try {
      if (!event || typeof event.type !== 'string') return;
      const key = (session && (session.id || session.sessionId)) || 'default';

      if (event.type === 'user/message') {
        if (isInjected(event.data)) return;
        const raw = textOf(event.data);
        if (!raw) return;
        const cwdMatch = raw.match(/Current working directory:\s*"([^"]+)"/);
        const prev = pending.get(key) || { user: '', assistant: [], cwd: '' };
        if (cwdMatch) {
          prev.cwd = cwdMatch[1];
          pending.set(key, prev);
          return;
        }
        const userText = cleanUserText(raw);
        if (isBoilerplate(raw) || !userText) return;
        scheduleRecall(userText);
        if (prev.assistant.length) pending.set(key, { user: userText, assistant: [], cwd: prev.cwd });
        else pending.set(key, { user: userText, assistant: [], cwd: prev.cwd || (session && (session.cwd || session.workspace?.cwd)) || '' });
        return;
      }

      if (event.type === 'assistant/message') {
        const state = pending.get(key);
        if (!state) return;
        const text = textOf(event.data);
        if (text) state.assistant.push(text);
        return;
      }

      if (event.type === 'turn/end') {
        const state = pending.get(key);
        if (!state) return;
        pending.delete(key);
        const reply = state.assistant.join('\n').trim();
        if (!state.user || !reply) {
          dbg('skip turn/end u=' + (state.user || '').length + ' a=' + reply.length);
          return;
        }
        const body = '用户: ' + state.user.slice(0, 1500) + '\n助手: ' + reply.slice(0, 1500);
        store
          .add({ text: body, cwd: state.cwd, session: String(key), kind: 'turn' })
          .then((id) => dbg('stored ' + id + ' len=' + body.length))
          .catch((e) => dbg('store-error ' + String(e).slice(0, 120)));
      }
    } catch {}
  });

  // ---- 工具 ----
  ctx.tools.register({
    name: 'memory_search',
    description: '语义检索跨会话长期记忆（本地 bge-m3 向量）。当需要回忆以前会话做过什么、用户偏好、历史决定时调用。',
    parameters: {
      type: 'object',
      additionalProperties: false,
      properties: {
        query: { type: 'string', description: '要检索的自然语言问题或关键词。' },
        k: { type: 'integer', description: '返回条数，默认 5。' },
      },
      required: ['query'],
    },
    output: {
      schema: {
        type: 'object',
        additionalProperties: false,
        required: ['results'],
        properties: {
          results: {
            type: 'array',
            items: {
              type: 'object',
              additionalProperties: false,
              required: ['text', 'score', 'ts', 'cwd'],
              properties: {
                text: { type: 'string' },
                score: { type: 'number' },
                ts: { type: 'integer' },
                cwd: { type: 'string' },
              },
            },
          },
        },
      },
      render: (_args, value) => [{
        type: 'text',
        text: value.results.length
          ? value.results.map((r, i) => `${i + 1}. [${stamp(r.ts)}] (${r.cwd || '?'}) ${r.score.toFixed(2)}\n${r.text.slice(0, 400)}`).join('\n\n')
          : '没有匹配的记忆。',
      }],
    },
    async execute(args) {
      const k = Number.isFinite(args.k) ? Math.max(1, Math.min(20, args.k)) : 5;
      const rows = await store.search(String(args.query ?? ''), k, 0.25);
      return { results: rows.map((r) => ({ text: r.text.slice(0, 1500), score: r.score, ts: r.ts, cwd: r.cwd })) };
    },
  });

  ctx.tools.register({
    name: 'memory_write',
    description: '把一条值得长期记住的事实/偏好/决定写入跨会话记忆（本地向量库）。只在信息有长期价值时使用，不要写流水账。',
    parameters: {
      type: 'object',
      additionalProperties: false,
      properties: {
        text: { type: 'string', description: '一句话事实，自包含、脱离上下文也能看懂。' },
      },
      required: ['text'],
    },
    output: {
      schema: {
        type: 'object',
        additionalProperties: false,
        required: ['saved', 'id'],
        properties: {
          saved: { type: 'boolean' },
          id: { type: 'string' },
        },
      },
      render: (_args, value) => [{ type: 'text', text: value.saved ? '已写入记忆 ' + value.id : '重复或太短，未写入。' }],
    },
    async execute(args) {
      const id = await store.add({ text: String(args.text ?? ''), kind: 'explicit' });
      return { saved: Boolean(id), id: id || '' };
    },
  });

  ctx.tools.register({
    name: 'memory_stats',
    description: '查看本地向量记忆的条数与配置。',
    parameters: { type: 'object', additionalProperties: false, properties: {} },
    output: {
      schema: {
        type: 'object',
        additionalProperties: false,
        required: ['count', 'file', 'model'],
        properties: {
          count: { type: 'integer' },
          file: { type: 'string' },
          model: { type: 'string' },
        },
      },
      render: (_args, value) => [{ type: 'text', text: `记忆条数 ${value.count}，模型 ${value.model}，文件 ${value.file}` }],
    },
    execute() {
      const s = store.stats();
      return { count: s.count, file: s.file, model: s.model };
    },
  });

  try {
    mkdirSync(dir, { recursive: true });
    appendFileSync(join(dir, 'plugin.log'), new Date().toISOString() + ' loaded tools=memory_search,memory_write,memory_stats dir=' + dir + '\n');
  } catch {}
}
