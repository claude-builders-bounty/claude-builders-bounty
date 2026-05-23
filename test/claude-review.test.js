import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import { heuristicReview, parseArgs, parsePullRequestUrl } from '../src/claude-review.js'

describe('parsePullRequestUrl', () => {
  it('parses GitHub pull request URLs', () => {
    assert.deepEqual(parsePullRequestUrl('https://github.com/owner/repo/pull/123'), {
      owner: 'owner',
      repo: 'repo',
      number: 123,
    })
  })

  it('rejects non-PR URLs', () => {
    assert.throws(() => parsePullRequestUrl('https://github.com/owner/repo/issues/123'), /Invalid GitHub PR URL/)
  })
})

describe('parseArgs', () => {
  it('parses common CLI options', () => {
    assert.deepEqual(parseArgs(['--pr', 'https://github.com/a/b/pull/1', '--mode', 'heuristic', '--post']), {
      pr: 'https://github.com/a/b/pull/1',
      mode: 'heuristic',
      post: true,
    })
  })
})

describe('heuristicReview', () => {
  it('emits the required structured Markdown sections', () => {
    const review = heuristicReview({
      prUrl: 'https://github.com/a/b/pull/1',
      title: 'Add auth middleware',
      diff: `diff --git a/src/auth.js b/src/auth.js
index 111..222 100644
--- a/src/auth.js
+++ b/src/auth.js
@@ -1,2 +1,4 @@
+const token = process.env.API_TOKEN
+export function isAdmin(user) { return user.role === 'admin' }
`,
    })

    assert.match(review, /## Summary/)
    assert.match(review, /## Identified risks/)
    assert.match(review, /## Improvement suggestions/)
    assert.match(review, /## Confidence/)
    assert.match(review, /Authentication or authorization paths appear affected/)
  })
})
