#!/usr/bin/env node
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const logPath = process.argv[2];
if (!logPath) throw new Error('Usage: node assert.js LOG_PATH');

const entries = fs.readFileSync(logPath, 'utf8').trim().split('\n').filter(Boolean).map(JSON.parse);
const requests = entries.filter((entry) => !entry.rawUrl.startsWith('/health'));
const fixture = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'prs-page-1.json'), 'utf8'));
const knownNumber = String(fixture.items[0].number);

const byPath = (pathname) => requests.filter((entry) => new URL(entry.rawUrl, 'http://localhost').pathname === pathname);
const githubRequests = requests.filter((entry) => entry.method === 'GET');
const activeGithubRequests = githubRequests.filter((entry) => entry.rawUrl.includes('microsoft%2Fvscode') || entry.rawUrl.includes('/microsoft/vscode/'));

assert(activeGithubRequests.some((entry) => entry.rawUrl.includes('/commits') && new URL(entry.rawUrl, 'http://localhost').searchParams.get('page') === '2'), 'commits page 2 was not requested');
assert(activeGithubRequests.some((entry) => (new URL(entry.rawUrl, 'http://localhost').searchParams.get('q') || '').includes('is:pr') && new URL(entry.rawUrl, 'http://localhost').searchParams.get('page') === '2'), 'merged PR page 2 was not requested');

for (const request of githubRequests) {
  assert.equal(request.headers.authorization, 'token mock-github-token', 'GitHub credential header mismatch');
  assert.equal(request.headers.accept, 'application/vnd.github+json', 'GitHub Accept header mismatch');
  assert.equal(request.headers['x-github-api-version'], '2022-11-28', 'GitHub API version header mismatch');
  const url = new URL(request.rawUrl, 'http://localhost');
  assert.equal(url.searchParams.get('per_page'), '100', 'GitHub per_page mismatch');
}

const prRequest = activeGithubRequests.find((entry) => (new URL(entry.rawUrl, 'http://localhost').searchParams.get('q') || '').includes('is:pr'));
assert(prRequest, 'merged PR request missing');
const prQuery = new URL(prRequest.rawUrl, 'http://localhost').searchParams.get('q');
assert.match(prQuery, /^repo:microsoft\/vscode is:pr is:merged merged:.*\+00:00\.\..*\+00:00$/, 'merged PR query or UTC range mismatch');
assert(prRequest.rawUrl.includes('%2B00%3A00'), 'the +00:00 offset was not URL-encoded');

const claudeRequests = byPath('/v1/messages');
assert.equal(claudeRequests.length, 2, 'quiet workflow should skip Claude');
for (const request of claudeRequests) {
  assert.equal(request.headers['x-api-key'], 'mock-anthropic-key', 'Anthropic credential header mismatch');
  assert.equal(request.headers['anthropic-version'], '2023-06-01', 'Anthropic version header mismatch');
  assert.equal(request.body.model, 'claude-sonnet-4-20250514', 'Claude model mismatch');
  assert.match(request.body.system, /in English/, 'configured language missing from Claude system prompt');
  assert.match(request.body.system, /untrusted/i, 'prompt-injection instruction missing');
}

const slackRequests = byPath('/slack');
assert.equal(slackRequests.length, 1, 'Slack should receive one payload');
const slack = slackRequests[0].body;
assert.equal(typeof slack.text, 'string');
assert.equal(slack.unfurl_links, false);
assert.equal(slack.unfurl_media, false);
assert(slack.text.includes(`<https://github.com/microsoft/vscode/issues/${knownNumber}|#${knownNumber}>`), 'known weekly number was not linked for Slack');
assert(slack.text.includes('#999999'), 'unknown number disappeared from Slack');
assert(!slack.text.includes('issues/999999'), 'unknown number was linked for Slack');

const discordRequests = byPath('/discord');
assert(discordRequests.length >= 2, 'long Discord response was not split');
for (const request of discordRequests) {
  assert(request.body.content.length <= 1900, `Discord chunk exceeded 1900 chars: ${request.body.content.length}`);
  assert.deepEqual(request.body.allowed_mentions, { parse: [] });
  assert.equal(request.body.flags, 4);
}
const discordText = discordRequests.map((entry) => entry.body.content).join('\n\n');
assert(discordText.includes(`[#${knownNumber}](https://github.com/microsoft/vscode/issues/${knownNumber})`), 'known weekly number was not linked for Discord');
assert(discordText.includes('#999999'), 'unknown number disappeared from Discord');
assert(!discordText.includes('issues/999999'), 'unknown number was linked for Discord');

const quietRequests = byPath('/quiet-fr');
assert.equal(quietRequests.length, 1, 'quiet FR workflow should send one payload');
assert.match(quietRequests[0].body.text, /Semaine calme pour microsoft\/empty-fixture/);
assert.match(quietRequests[0].body.text, /Totaux : 0 commit/);

process.stdout.write([
  'PASS: n8n requested page 2 for commits and merged PRs',
  'PASS: GitHub and Anthropic authentication headers are correct',
  'PASS: UTC search offsets remain +00:00 after URL decoding',
  'PASS: Claude received the configured model and English instruction',
  'PASS: Slack payload is valid and links only weekly issue numbers',
  `PASS: ${discordRequests.length} Discord chunks are at most 1900 characters with mentions disabled`,
  'PASS: quiet activity skipped Claude and produced the fixed French text',
].join('\n') + '\n');
