const test = require('node:test');
const assert = require('node:assert/strict');
const { categorizeCommit } = require('../generate_changelog.js');

test('categorizeCommit recognizes conventional commits', () => {
  assert.deepEqual(categorizeCommit('feat(auth): implement oauth2 token rotation'), {
    category: 'Added',
    message: 'implement oauth2 token rotation'
  });

  assert.deepEqual(categorizeCommit('fix: resolve null pointer exception in parser'), {
    category: 'Fixed',
    message: 'resolve null pointer exception in parser'
  });

  assert.deepEqual(categorizeCommit('docs: add 3-step setup guide'), {
    category: 'Documentation',
    message: 'add 3-step setup guide'
  });

  assert.deepEqual(categorizeCommit('security: sanitize shell inputs'), {
    category: 'Security',
    message: 'sanitize shell inputs'
  });

  assert.deepEqual(categorizeCommit('refactor(core): streamline category mapping'), {
    category: 'Changed',
    message: 'streamline category mapping'
  });
});

test('categorizeCommit falls back to keyword matching', () => {
  assert.equal(categorizeCommit('Add new test cases for validator').category, 'Added');
  assert.equal(categorizeCommit('Patch memory leak in cache layer').category, 'Fixed');
  assert.equal(categorizeCommit('Update dependency versions in package.json').category, 'Changed');
});
