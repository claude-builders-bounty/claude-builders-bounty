// verify.mjs — validates the workflow against the bounty's acceptance criteria.
// Run: node verify.mjs   (exits 0 on pass, 1 on fail)
import fs from "node:fs";

const wf = JSON.parse(fs.readFileSync(new URL("./workflow.json", import.meta.url), "utf8"));
const byName = Object.fromEntries(wf.nodes.map(n => [n.name, n]));
const types = wf.nodes.map(n => n.type);
const has = (t) => types.includes(t);

const checks = {
  "parses as JSON": true,
  "has a workflow id — n8n's CLI importer rejects the file without one": typeof wf.id === "string" && wf.id.length > 0,
  "declares meta (round-trip fidelity)": !!wf.meta,
  "has exactly the 6 expected nodes": wf.nodes.length === 6,
  "has a schedule trigger": has("n8n-nodes-base.scheduleTrigger"),
  "cron = Friday 17:00": /0 17 \* \* 5/.test(JSON.stringify(byName["Weekly Trigger (Fri 17:00)"]?.parameters)),
  "has a code node (GitHub fetch + assemble)": has("n8n-nodes-base.code"),
  "calls the Claude API": /api\.anthropic\.com\/v1\/messages/.test(JSON.stringify(wf)),
  "pins claude-sonnet-4-20250514": /claude-sonnet-4-20250514/.test(JSON.stringify(wf)),
  "fetches commits": /\/commits\?since=/.test(JSON.stringify(wf)),
  "fetches closed issues": /\/issues\?state=closed/.test(JSON.stringify(wf)),
  "fetches merged PRs": /\/pulls\?state=closed/.test(JSON.stringify(wf)),
  "configurable repo owner/name": /repo_owner/.test(JSON.stringify(wf)) && /repo_name/.test(JSON.stringify(wf)),
  "configurable language EN/FR": /language/.test(JSON.stringify(wf)) && /French/.test(JSON.stringify(wf)),
  "secrets via $env, not hardcoded": /\$env\.ANTHROPIC_API_KEY/.test(JSON.stringify(wf)) && !/sk-ant-[A-Za-z0-9]/.test(JSON.stringify(wf)),
  "delivers via webhook (Discord or Slack)": /discord_webhook/.test(JSON.stringify(wf)) && /content:/.test(JSON.stringify(wf)) && /text:/.test(JSON.stringify(wf)),
  "linear connections, all nodes wired": wf.nodes.every(n => wf.connections[n.name] || n.name === "Deliver (Discord or Slack)")
};

// syntax-check every embedded jsCode (top-level await wrapped in an async IIFE)
let codeOk = true, codeErr = "";
for (const n of wf.nodes.filter(x => x.type === "n8n-nodes-base.code")) {
  try { new Function("$input", "$env", "return (async()=>{\n" + n.parameters.jsCode + "\n})()"); }
  catch (e) { codeOk = false; codeErr = n.name + ": " + e.message; }
}
checks["every Code node's JS is syntactically valid"] = codeOk;

// --- execute the GitHub-collection Code node for real, against a stubbed httpRequest ---
// (syntax alone proves nothing about the filtering/assembly logic)
const DAY = 86400000;
const collectSrc = byName["Collect GitHub Activity"].parameters.jsCode;
const runCollect = new Function("$input", "$env", "return (async()=>{\n" + collectSrc + "\n})()");

function stubCall({ failPaths = [] } = {}) {
  const seen = [];
  const httpRequest = async ({ url, headers }) => {
    seen.push({ url, headers });
    if (failPaths.some(p => url.includes(p))) throw new Error("simulated " + url);
    if (url.includes("/commits?")) return [
      { sha: "abcdef1234567", commit: { message: "feat: add thing\n\nbody text" } },
      { sha: "0123456789abc", commit: { message: "fix: correct thing" } }
    ];
    if (url.includes("/issues?")) return [
      { number: 1, title: "a closed issue" },
      { number: 2, title: "a PR — the issues endpoint returns these too", pull_request: {} }
    ];
    if (url.includes("/pulls?")) return [
      { number: 3, title: "merged inside the window", merged_at: new Date(Date.now() - DAY).toISOString(), user: { login: "amp" } },
      { number: 4, title: "merged long ago", merged_at: new Date(Date.now() - 30 * DAY).toISOString(), user: { login: "old" } },
      { number: 5, title: "closed but never merged", merged_at: null, user: { login: "nope" } }
    ];
    return [];
  };
  return { seen, httpRequest };
}

const cfg = { repo_owner: "acme", repo_name: "app", language: "en", days: 7, discord_webhook: "https://x" };

let rtOk = true, rtErr = "";
let out = null;
try {
  const stub = stubCall();
  out = await runCollect.call({ helpers: { httpRequest: stub.httpRequest } }, { first: () => ({ json: cfg }) }, { GITHUB_TOKEN: "t" });
} catch (e) { rtOk = false; rtErr = e.message; }

checks["code node runs to completion and returns one item"] = rtOk && out?.length === 1 && !!out[0].json;

if (rtOk && out) {
  const j = out[0].json;
  checks["counts commits in the window"] = j.counts.commits === 2;
  checks["drops PRs from the issues endpoint (issues count = 1, not 2)"] = j.counts.issues === 1;
  checks["drops unmerged + out-of-window PRs (prs count = 1, not 3)"] = j.counts.prs === 1;
  checks["digest names the repo + the real PR only"] = /Repo: acme\/app/.test(j.prompt) && /- #3 /.test(j.prompt) && !/- #4 /.test(j.prompt) && !/- #5 /.test(j.prompt);
  checks["prompt asks for English, 150-250 words, invent nothing"] = /English/.test(j.prompt) && /150-250 words/.test(j.prompt) && /invent nothing/.test(j.prompt);
  const frCfg = { ...cfg, language: "fr" };
  const frOut = await runCollect.call({ helpers: { httpRequest: stubCall().httpRequest } }, { first: () => ({ json: frCfg }) }, {});
  checks["language=fr switches the prompt to French"] = /French/.test(frOut[0].json.prompt) && !/English/.test(frOut[0].json.prompt);
}

// a rate-limited / 404ing endpoint must degrade to an empty list, not blow up the run
try {
  const bad = stubCall({ failPaths: ["/pulls?"] });
  const out2 = await runCollect.call({ helpers: { httpRequest: bad.httpRequest } }, { first: () => ({ json: cfg }) }, {});
  checks["a failing GitHub call degrades to an empty list instead of throwing"] = out2[0].json.counts.prs === 0 && out2[0].json.counts.commits === 2;
} catch (e) { checks["a failing GitHub call degrades to an empty list instead of throwing"] = false; }

// the auth header: present only when an env token exists, and never baked into the JSON
{
  const withTok = stubCall();
  await runCollect.call({ helpers: { httpRequest: withTok.httpRequest } }, { first: () => ({ json: cfg }) }, { GITHUB_TOKEN: "secret" });
  const noTok = stubCall();
  await runCollect.call({ helpers: { httpRequest: noTok.httpRequest } }, { first: () => ({ json: cfg }) }, {});
  checks["sends Authorization only when GITHUB_TOKEN is set"] =
    withTok.seen.every(c => c.headers.Authorization === "Bearer secret") &&
    noTok.seen.every(c => !("Authorization" in c.headers)) &&
    withTok.seen.length === 3;
}

if (!rtOk) console.log("     -> runtime: " + rtErr);

let pass = true;
for (const [k, v] of Object.entries(checks)) { if (!v) pass = false; console.log((v ? "OK  " : "FAIL") + "  " + k); }
if (!codeOk) console.log("     -> " + codeErr);
console.log(pass ? "\nALL CHECKS PASS" : "\nCHECKS FAILED");
process.exit(pass ? 0 : 1);
