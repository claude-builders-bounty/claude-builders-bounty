import assert from 'node:assert/strict';
import {mkdtempSync, readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {test} from 'node:test';

import {
  buildBlockResponse,
  findBlockedPattern,
  getCommandFromHookInput,
  logBlockedAttempt,
} from '../hooks/pre-tool-use/block-dangerous-bash.js';

test('extracts bash command from Claude Code hook payload', () => {
  const payload = JSON.stringify({
    tool_name: 'Bash',
    tool_input: {command: 'npm test'},
  });

  assert.equal(getCommandFromHookInput(payload), 'npm test');
});

test('ignores non-bash tools', () => {
  const payload = JSON.stringify({
    tool_name: 'Read',
    tool_input: {command: 'rm -rf dist'},
  });

  assert.equal(getCommandFromHookInput(payload), '');
});

test('blocks dangerous bash patterns', () => {
  const cases = [
    ['rm -rf node_modules', 'rm -rf'],
    ['psql -c "DROP TABLE users"', 'DROP TABLE'],
    ['git push origin main --force', 'git push --force'],
    ['sqlite3 app.db "TRUNCATE sessions"', 'TRUNCATE'],
    ['sqlite3 app.db "DELETE FROM users"', 'DELETE FROM without WHERE'],
  ];

  for (const [command, name] of cases) {
    assert.equal(findBlockedPattern(command)?.name, name);
  }
});

test('allows normal commands and scoped deletes', () => {
  const cases = [
    'npm test',
    'git push origin feature/hook',
    'sqlite3 app.db "DELETE FROM users WHERE id = 1"',
    'rm -r dist',
  ];

  for (const command of cases) {
    assert.equal(findBlockedPattern(command), null);
  }
});

test('builds Claude-readable block response', () => {
  const blocker = findBlockedPattern('rm -rf .');
  const response = buildBlockResponse(blocker, 'rm -rf .');

  assert.equal(response.decision, 'block');
  assert.match(response.reason, /Blocked dangerous bash command/);
});

test('logs blocked attempts as json lines', () => {
  const dir = mkdtempSync(join(tmpdir(), 'claude-hook-'));
  const logPath = join(dir, 'blocked.log');
  const blocker = findBlockedPattern('DROP TABLE users');

  logBlockedAttempt({
    command: 'DROP TABLE users',
    blocker,
    cwd: '/tmp/example-project',
    logPath,
  });

  const [line] = readFileSync(logPath, 'utf8').trim().split('\n');
  const record = JSON.parse(line);

  assert.equal(record.pattern, 'DROP TABLE');
  assert.equal(record.command, 'DROP TABLE users');
  assert.equal(record.project_path, '/tmp/example-project');
  assert.match(record.timestamp, /^\d{4}-\d{2}-\d{2}T/);
});
