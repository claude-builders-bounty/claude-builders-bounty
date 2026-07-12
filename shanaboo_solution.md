Based on the issue, I need to create a PR review agent. Since the repo only shows README.md and LICENSE, I'll create the necessary files for the Claude Code sub-agent that reviews PRs and posts structured Markdown comments.

```diff
--- /dev/null
+++ b/agents/claude-review/claude-review.js
@@ -0,0 +1,284 @@
+#!/usr/bin/env node
+
+/**
+ * claude-review — Claude Code sub-agent for PR review
+ * 
+ * Usage:
+ *   claude-review --pr https://github.com/owner/repo/pull/123
+ *   claude-review --diff ./path/to/diff.patch
+ *   claude-review --repo owner/repo --pr 123
+ * 
+ * Outputs a structured Markdown review comment to stdout.
+ */
+
+const { execSync } = require('child_process');
+const fs = require('fs');
+const path = require('path');
+const https = require('https');
+
+// ─── CLI argument parsing ───────────────────────────────────────────
+function parseArgs() {
+  const args = process.argv.slice(2);
+  const opts = {
+    prUrl: null,
+    diffFile: null,
+    repo: null,
+    prNumber: null,
+    outputFile: null,
+    token: process.env.GITHUB_TOKEN || process.env.GH_TOKEN || null,
+  };
+
+  for (let i = 0; i < args.length; i++) {
+    switch (args[i]) {
+      case '--pr':
+        opts.prUrl = args[++i];
+        break;
+      case '--diff':
+        opts.diffFile = args[++i];
+        break;
+      case '--repo':
+        opts.repo = args[++i];
+        break;
+      case '--pr-number':
+        opts.prNumber = args[++i];
+        break;
+      case '--output':
+        opts.outputFile = args[++i];
+        break;
+      case '--token':
+        opts.token = args[++i];
+        break;
+      case '--help':
+      case '-h':
+        printHelp();
+        process.exit(0);
+      default:
+        console.error(`Unknown argument: ${args[i]}`);
+        printHelp();
+        process.exit(1);
+    }
+  }
+
+  return opts;
+}
+
+function printHelp() {
+  console.log(`
+claude-review — Claude Code PR review agent
+
+Usage:
+  claude-review --pr <PR_URL>
+  claude-review --diff <DIFF_FILE>
+  claude-review --repo <OWNER/REPO> --pr-number <NUM>
+
+Options:
+  --pr <URL>         Full GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)
+  --diff <FILE>      Path to a local diff/patch file
+  --repo <OWNER/REPO>  Repository slug
+  --pr-number <NUM>  Pull request number
+  --output <FILE>    Write review to file instead of stdout
+  --token <TOKEN>    GitHub personal access token (or set GITHUB_TOKEN env var)
+  --help, -h         Show this help
+
+Environment:
+  GITHUB_TOKEN       GitHub token for API access (optional, for posting comments)
+`);
+}
+
+// ─── GitHub API helpers ─────────────────────────────────────────────
+function githubApiRequest(endpoint, token, method = 'GET', body = null) {
+  return new Promise((resolve, reject) => {
+    const url = new URL(endpoint, 'https://api.github.com');
+    const options = {
+      hostname: url.hostname,
+      path: url.pathname + url.search,
+      method,
+      headers: {
+        'User-Agent': 'claude-review-agent/1.0',
+        'Accept': 'application/vnd.github.v3+json',
+        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
+      },
+    };
+
+    const req = https.request(options, (res) => {
+      let data = '';
+      res.on('data', chunk => data += chunk);
+      res.on('end', () => {
+        if (res.statusCode >= 200 && res.statusCode < 300) {
+          try {
+            resolve(JSON.parse(data));
+          } catch {
+            resolve(data);
+          }
+        } else {
+          reject(new Error(`GitHub API error ${res.statusCode}: ${data}`));
+        }
+      });
+    });
+
+    req.on('error', reject);
+    if (body) req.write(JSON.stringify(body));
+    req.end();
+  });
+}
+
+async function fetchPrDiff(repo, prNumber, token) {
+  const endpoint = `/repos/${repo}/pulls/${prNumber}`;
+  // GitHub returns diff via .diff media type
+  const url = new URL(endpoint, 'https://api.github.com');
+  
+  return new Promise((resolve, reject) => {
+    const options = {
+      hostname: url.hostname,
+      path: url.pathname,
+      method: 'GET',
+      headers: {
+        'User-Agent': 'claude-review-agent/1.0',
+        'Accept': 'application/vnd.github.v3.diff',
+        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
+      },
+    };
+
+    const req = https.request(options, (res) => {
+      let data = '';
+      res.on('data', chunk => data += chunk);
+      res.on('end', () => {
+        if (res.statusCode >= 200 && res.statusCode < 300) {
+          resolve(data);
+        } else {
+          reject(new Error(`GitHub API error ${res.statusCode}: ${data}`));
+        }
+      });
+    });
+
+    req.on('error', reject);
+    req.end();
+  });
+}
+
+async function fetchPrInfo(repo, prNumber, token) {
+  const endpoint = `/repos/${repo}/pulls/${prNumber}`;
+  return githubApiRequest(endpoint, token);
+}
+
+async function postReviewComment(repo, prNumber, body, token) {
+  const endpoint = `/repos/${repo}/issues/${prNumber}/comments`;
+  return githubApiRequest(endpoint, token, 'POST', { body });
+}
+
+// ─── Diff analysis ──────────────────────────────────────────────────
+function analyzeDiff(diffText) {
+ 