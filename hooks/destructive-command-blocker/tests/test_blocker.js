const test = require('node:test');
const assert = require('node:assert/strict');
const { checkCommand } = require('../pre_tool_use.js');

test('blocks dangerous rm -rf commands', () => {
  assert.equal(checkCommand('rm -rf /var/www').allowed, false);
  assert.equal(checkCommand('rm -fr ./node_modules').allowed, false);
  assert.equal(checkCommand('rm -r -f build/').allowed, false);
});

test('blocks database destructive statements', () => {
  assert.equal(checkCommand('psql -c "DROP TABLE users;"').allowed, false);
  assert.equal(checkCommand('sqlite3 db.sqlite "TRUNCATE TABLE accounts"').allowed, false);
  assert.equal(checkCommand('DELETE FROM users').allowed, false);
});

test('blocks forced git push', () => {
  assert.equal(checkCommand('git push origin main --force').allowed, false);
  assert.equal(checkCommand('git push -f origin main').allowed, false);
});

test('allows safe and routine development commands', () => {
  assert.equal(checkCommand('npm run dev').allowed, true);
  assert.equal(checkCommand('git commit -m "feat: add feature"').allowed, true);
  assert.equal(checkCommand('git status').allowed, true);
  assert.equal(checkCommand('rm temp.txt').allowed, true);
  assert.equal(checkCommand('DELETE FROM users WHERE id = 123;').allowed, true);
});
