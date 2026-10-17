/**
 * Tests for the analysis core. Run: node --test
 * Uses only node:test + node:assert (stdlib), no dependencies.
 */

import test from "node:test";
import assert from "node:assert/strict";
import { analyzePr, renderMarkdown } from "../src/analyze.mjs";

const file = (filename, additions = 10, deletions = 0, patch = "", status = "modified") => ({
  filename,
  status,
  additions,
  deletions,
  patch: patch || `@@ -1,3 +1,3 @@\n context\n-old line\n+new line`,
});

const meta = (over = {}) => ({
  title: "feat: add thing",
  body: "A description that is comfortably longer than forty characters so it counts as present.",
  additions: 10,
  deletions: 2,
  user: "octocat",
  draft: false,
  ...over,
});

test("clean, small, tested PR scores High and reports no risks", () => {
  const files = [file("src/thing.mjs"), file("test/thing.test.mjs")];
  const r = analyzePr(meta(), files);
  assert.equal(r.confidence, "High");
  assert.deepEqual(r.risks, []);
  assert.match(r.summary, /adds functionality/);
});

test("source change without tests raises a risk and a suggestion", () => {
  const r = analyzePr(meta(), [file("src/thing.mjs")]);
  assert.ok(r.risks.some((x) => /No test files changed/.test(x)));
  assert.ok(r.suggestions.some((x) => /at least one test/.test(x)));
});

test("migration, lockfile, CI and auth files each raise their own risk", () => {
  const files = [
    file("db/migrations/004_add_users.sql"),
    file("package-lock.json"),
    file(".github/workflows/ci.yml"),
    file("src/auth/session.mjs"),
    file("test/a.test.mjs"),
  ];
  const r = analyzePr(meta(), files);
  const joined = r.risks.join("\n");
  assert.match(joined, /Schema\/data change/);
  assert.match(joined, /Lockfile committed/);
  assert.match(joined, /CI workflow change/);
  assert.match(joined, /Auth surface touched/);
});

test("added or removed lines become one risk", () => {
  const files = [file("src/big.mjs", 900, 300, "@@ \n line\n+x")];
  const r = analyzePr(meta({ additions: 900, deletions: 300 }), files);
  assert.ok(r.risks.some((x) => /Very large diff/.test(x)));
  assert.equal(r.confidence, "Low");
  assert.ok(r.suggestions.some((x) => /Split into stacked PRs/.test(x)));
});

test("patch signals: secret, password assignment flags, empty catch, TODO, debug", () => {
  const files = [
    file(
      "src/config.mjs",
      5,
      0,
      ["@@ ", "+const api_key = 'sk_live_abcdef1234567890';", "+try { go() } catch (e) {}", "+// TODO: wire this up", "+console.log('here')"].join("\n")
    ),
    file("test/config.test.mjs"),
  ];
  const r = analyzePr(meta(), files);
  const joined = [...r.risks, ...r.suggestions].join("\n");
  assert.match(joined, /hardcoded credential/);
  assert.match(joined, /Empty catch block/);
  assert.match(joined, /TODOs into linked issues/);
  assert.match(joined, /debug output/);
});

test("credential that comes from the environment is not flagged", () => {
  const files = [file("src/x.mjs", 5, 0, "@@ \n+const key = process.env.SOME_TOKEN_abcdef123456;"), file("t/spec.mjs")];
  const r = analyzePr(meta(), files);
  assert.ok(!r.risks.some((x) => /hardcoded credential/.test(x)));
});

test("deleted file and draft PR are called out", () => {
  const files = [file("src/old.mjs", 0, 40, "@@ \n-x", "removed")];
  const r = analyzePr(meta({ draft: true }), files);
  const joined = r.risks.join("\n");
  assert.match(joined, /File deletion/);
  assert.match(joined, /Still a draft/);
});

test("thin description is both a risk-free note in the summary and a suggestion", () => {
  const r = analyzePr(meta({ body: "fix" }), [file("src/a.mjs"), file("t/a.test.mjs")]);
  assert.match(r.summary, /description is thin/);
  assert.ok(r.suggestions.some((x) => /Expand the PR description/.test(x)));
  assert.equal(r.confidence, "Medium");
});

test("broken CI patch is skipped without throwing", () => {
  const files = [
    { filename: "src/a.mjs", status: "modified", additions: 1, deletions: 1, patch: null },
    { filename: "assets/logo.png", status: "added", additions: 0, deletions: 0, patch: null },
    file("t/a.test.mjs"),
  ];
  const r = analyzePr(meta(), files);
  assert.ok(r.risks.some((x) => /Binary file/.test(x)));
});

test("rendered markdown carries every required section and the confidence score", () => {
  const files = [file("src/x.mjs"), file("test/x.test.mjs")];
  const md = renderMarkdown(meta(), files, analyzePr(meta(), files));
  for (const h of ["### Summary", "### Risks", "### Improvement suggestions", "### Confidence"]) {
    assert.ok(md.includes(h), `missing ${h}`);
  }
  assert.match(md, /\*\*High\*\*/);
  assert.match(md, /1 file\(s\)|2 file\(s\)/);
});

test("markdown output still renders when there are no risks or suggestions", () => {
  const files = [file("src/x.mjs"), file("test/x.test.mjs")];
  // a chore title with tests and a full description produces neither bucket
  const m = meta({ title: "chore: bump tooling" });
  const md = renderMarkdown(m, files, analyzePr(m, files), { footer: false });
  assert.match(md, /No structural risk detected/);
  assert.match(md, /Nothing notable/);
  assert.ok(!md.includes("Generated by"));
});
