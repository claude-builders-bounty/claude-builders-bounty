import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const workflow = JSON.parse(readFileSync(new URL('./weekly-github-claude-summary.workflow.json', import.meta.url), 'utf8'));
const code = workflow.nodes.find(node => node.name === 'Prepare Discord Message').parameters.jsCode;
const activity = { repository: 'acme/test', period: { since: '2026-10-16', until: '2026-10-23' } };
const deliver = response => new Function('$', '$json', code)(() => ({ first: () => ({ json: activity }) }), response)[0].json.message;

for (const [name, response] of [
  ['absent content', {}],
  ['empty content', { content: [] }],
  ['non-array content', { content: {} }],
  ['empty text', { content: [{ type: 'text', text: '' }] }],
  ['whitespace text', { content: [{ type: 'text', text: ' \n\t ' }] }],
  ['non-text blocks', { content: [{ type: 'thinking', thinking: 'private' }] }],
]) {
  test(`rejects ${name} before Discord delivery`, () => {
    assert.throws(() => deliver(response), /Claude returned no usable text summary/);
  });
}

test('preserves all text blocks and ignores non-text content', () => {
  const message = deliver({ content: [null, { type: 'thinking', thinking: 'private' }, { type: 'text', text: 'First highlight' }, { type: 'text', text: 'Second highlight' }] });
  assert.ok(message.endsWith('First highlight\n\nSecond highlight'));
  assert.ok(!message.includes('private'));
});

test('retains the Discord size boundary and truncation disclosure', () => {
  const message = deliver({ content: [{ type: 'text', text: 'x'.repeat(3000) }] });
  assert.equal(message.length, 1900);
  assert.ok(message.endsWith('_Trimmed to fit Discord._'));
});
