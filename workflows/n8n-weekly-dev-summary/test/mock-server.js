#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');

const logPath = process.argv[2];
if (!logPath) throw new Error('Usage: node mock-server.js LOG_PATH');

const fixtures = path.join(__dirname, 'fixtures');
const readFixture = (name) => JSON.parse(fs.readFileSync(path.join(fixtures, name), 'utf8'));
const commitsPage1 = readFixture('commits-page-1.json');
const commitsPage2 = readFixture('commits-page-2.json');
const prsPage1 = readFixture('prs-page-1.json');
const prsPage2 = readFixture('prs-page-2.json');
const issuesPage1 = readFixture('issues-page-1.json');
const knownNumber = prsPage1.items[0].number;

const readBody = async (request) => {
  const chunks = [];
  for await (const chunk of request) chunks.push(chunk);
  return Buffer.concat(chunks).toString('utf8');
};

const reply = (response, status, value) => {
  const body = JSON.stringify(value);
  response.writeHead(status, {
    'content-type': 'application/json',
    'content-length': Buffer.byteLength(body),
  });
  response.end(body);
};

const server = http.createServer(async (request, response) => {
  const bodyText = await readBody(request);
  let body = null;
  if (bodyText) {
    try {
      body = JSON.parse(bodyText);
    } catch {
      body = bodyText;
    }
  }
  const entry = {
    method: request.method,
    rawUrl: request.url,
    headers: request.headers,
    body,
  };
  fs.appendFileSync(logPath, `${JSON.stringify(entry)}\n`);

  const url = new URL(request.url, 'http://localhost');
  const page = Number(url.searchParams.get('page') || '1');

  if (request.method === 'GET' && url.pathname === '/health') return reply(response, 200, { ok: true });

  if (request.method === 'GET' && url.pathname.endsWith('/commits')) {
    if (url.pathname.includes('/empty-fixture/')) return reply(response, 200, []);
    if (page === 1) return reply(response, 200, commitsPage1);
    if (page === 2) return reply(response, 200, commitsPage2);
    return reply(response, 200, []);
  }

  if (request.method === 'GET' && url.pathname === '/search/issues') {
    const query = url.searchParams.get('q') || '';
    if (query.includes('repo:microsoft/empty-fixture')) {
      return reply(response, 200, { total_count: 0, incomplete_results: false, items: [] });
    }
    if (query.includes('is:pr')) {
      if (page === 1) return reply(response, 200, prsPage1);
      if (page === 2) return reply(response, 200, prsPage2);
      return reply(response, 200, { total_count: prsPage1.total_count, incomplete_results: false, items: [] });
    }
    if (query.includes('is:issue')) return reply(response, 200, issuesPage1);
  }

  if (request.method === 'POST' && url.pathname === '/v1/messages') {
    const longParagraph = Array.from(
      { length: 85 },
      (_, index) => `Verified detail ${index + 1} remains plain repository context and contains no delivery instructions.`,
    ).join(' ');
    const text = [
      `**Weekly work around #${knownNumber} and @microsoft**`,
      `The recorded activity includes #${knownNumber}. The deliberately unknown #999999 must remain unlinked.`,
      longParagraph,
      '**Totals: 103 commits · 103 merged PRs · 10 closed issues**',
    ].join('\n\n');
    return reply(response, 200, {
      id: 'msg_mock_weekly_summary',
      type: 'message',
      role: 'assistant',
      content: [{ type: 'text', text }],
      model: body?.model,
      stop_reason: 'end_turn',
      usage: { input_tokens: 100, output_tokens: 200 },
    });
  }

  if (request.method === 'POST' && ['/slack', '/discord', '/quiet-fr'].includes(url.pathname)) {
    return reply(response, 200, { ok: true });
  }

  return reply(response, 404, { error: `Unhandled ${request.method} ${request.url}` });
});

server.listen(34567, '0.0.0.0', () => process.stdout.write('READY\n'));

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => server.close(() => process.exit(0)));
}
