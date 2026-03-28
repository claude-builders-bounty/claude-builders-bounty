#!/usr/bin/env node
/**
 * claude-review — AI-powered PR reviewer using Claude (Anthropic)
 * Usage: claude-review --pr https://github.com/owner/repo/pull/123
 *        claude-review --pr https://github.com/owner/repo/pull/123 --provider gemini
 */

const { execSync, spawnSync } = require("child_process");
const https = require("https");
const http = require("http");

// ─── CLI Arg Parsing ──────────────────────────────────────────────────────────
const args = process.argv.slice(2);
let prUrl = null;
let provider = "anthropic"; // default
let model = null;
let verbose = false;
let outputFormat = "markdown"; // markdown | json

for (let i = 0; i < args.length; i++) {
  if (args[i] === "--pr" && args[i + 1]) prUrl = args[++i];
  else if (args[i] === "--provider" && args[i + 1]) provider = args[++i];
  else if (args[i] === "--model" && args[i + 1]) model = args[++i];
  else if (args[i] === "--json") outputFormat = "json";
  else if (args[i] === "--verbose" || args[i] === "-v") verbose = true;
  else if (args[i] === "--help" || args[i] === "-h") {
    printHelp();
    process.exit(0);
  } else if (!prUrl && args[i].startsWith("https://github.com")) {
    // allow positional URL
    prUrl = args[i];
  }
}

function printHelp() {
  console.log(`
claude-review — AI-powered PR reviewer

USAGE:
  claude-review --pr <github-pr-url> [options]

OPTIONS:
  --pr <url>          GitHub PR URL (required)
                      e.g. https://github.com/owner/repo/pull/123
  --provider <name>   LLM provider: anthropic (default) | gemini | groq
  --model <name>      Override default model
  --json              Output raw JSON instead of Markdown
  --verbose, -v       Print debug info
  --help, -h          Show this help

ENVIRONMENT VARIABLES:
  ANTHROPIC_API_KEY   Required when using --provider anthropic
  GEMINI_API_KEY      Required when using --provider gemini
  GROQ_API_KEY        Required when using --provider groq
  GITHUB_TOKEN        Optional — increases GitHub API rate limits

EXAMPLES:
  export ANTHROPIC_API_KEY=sk-ant-...
  claude-review --pr https://github.com/microsoft/vscode/pull/305897

  export GROQ_API_KEY=gsk_...
  claude-review --pr https://github.com/owner/repo/pull/42 --provider groq
`);
}

// ─── Validate inputs ──────────────────────────────────────────────────────────
if (!prUrl) {
  console.error("❌ Error: --pr <url> is required\n");
  printHelp();
  process.exit(1);
}

const prMatch = prUrl.match(
  /github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/
);
if (!prMatch) {
  console.error(
    "❌ Error: Invalid PR URL. Expected: https://github.com/owner/repo/pull/N"
  );
  process.exit(1);
}

const [, owner, repo, prNumber] = prMatch;

// ─── Provider config ─────────────────────────────────────────────────────────
const PROVIDERS = {
  anthropic: {
    apiKey: process.env.ANTHROPIC_API_KEY,
    defaultModel: "claude-sonnet-4-5",
    envVar: "ANTHROPIC_API_KEY",
  },
  gemini: {
    apiKey: process.env.GEMINI_API_KEY,
    defaultModel: "gemini-2.0-flash",
    envVar: "GEMINI_API_KEY",
  },
  groq: {
    apiKey: process.env.GROQ_API_KEY,
    defaultModel: "llama-3.3-70b-versatile",
    envVar: "GROQ_API_KEY",
  },
};

const providerConfig = PROVIDERS[provider];
if (!providerConfig) {
  console.error(
    `❌ Unknown provider: ${provider}. Supported: ${Object.keys(PROVIDERS).join(", ")}`
  );
  process.exit(1);
}

if (!providerConfig.apiKey) {
  console.error(
    `❌ Missing API key. Set ${providerConfig.envVar} environment variable.`
  );
  process.exit(1);
}

const activeModel = model || providerConfig.defaultModel;

// ─── Utilities ────────────────────────────────────────────────────────────────
function log(...args) {
  if (verbose) console.error("[verbose]", ...args);
}

function httpsPost(hostname, path, headers, body) {
  return new Promise((resolve, reject) => {
    const bodyStr = JSON.stringify(body);
    const options = {
      hostname,
      path,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(bodyStr),
        ...headers,
      },
    };
    const req = https.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch (e) {
          resolve({ status: res.statusCode, body: data });
        }
      });
    });
    req.on("error", reject);
    req.write(bodyStr);
    req.end();
  });
}

function httpsGet(hostname, path, headers = {}) {
  return new Promise((resolve, reject) => {
    const options = { hostname, path, method: "GET", headers };
    const req = https.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data), raw: data });
        } catch (e) {
          resolve({ status: res.statusCode, body: null, raw: data });
        }
      });
    });
    req.on("error", reject);
    req.end();
  });
}

// ─── Step 1: Fetch PR metadata + diff ────────────────────────────────────────
async function fetchPRData() {
  log(`Fetching PR #${prNumber} from ${owner}/${repo}...`);

  const ghToken = process.env.GITHUB_TOKEN || process.env.GH_TOKEN;
  const baseHeaders = {
    Accept: "application/vnd.github.v3+json",
    "User-Agent": "claude-review/1.0",
    ...(ghToken ? { Authorization: `token ${ghToken}` } : {}),
  };

  // Try gh CLI first (faster, handles auth automatically)
  let diff = null;
  try {
    const result = spawnSync(
      "gh",
      ["pr", "diff", prNumber, "--repo", `${owner}/${repo}`],
      { encoding: "utf8", timeout: 30000 }
    );
    if (result.status === 0 && result.stdout) {
      diff = result.stdout;
      log("Got diff via gh CLI");
    }
  } catch (e) {
    log("gh CLI not available, falling back to API");
  }

  // Fallback: GitHub API diff
  if (!diff) {
    const diffRes = await httpsGet(
      "api.github.com",
      `/repos/${owner}/${repo}/pulls/${prNumber}`,
      { ...baseHeaders, Accept: "application/vnd.github.v3.diff" }
    );
    if (diffRes.status !== 200) {
      throw new Error(
        `GitHub API error ${diffRes.status}: ${diffRes.raw.slice(0, 200)}`
      );
    }
    diff = diffRes.raw;
    log("Got diff via GitHub API");
  }

  // PR metadata
  const metaRes = await httpsGet(
    "api.github.com",
    `/repos/${owner}/${repo}/pulls/${prNumber}`,
    baseHeaders
  );

  let prMeta = {};
  if (metaRes.status === 200 && metaRes.body) {
    prMeta = {
      title: metaRes.body.title,
      body: metaRes.body.body || "",
      author: metaRes.body.user?.login,
      baseBranch: metaRes.body.base?.ref,
      headBranch: metaRes.body.head?.ref,
      changedFiles: metaRes.body.changed_files,
      additions: metaRes.body.additions,
      deletions: metaRes.body.deletions,
    };
    log("Got PR metadata:", JSON.stringify(prMeta));
  }

  return { diff, prMeta };
}

// ─── Step 2: Build the analysis prompt ───────────────────────────────────────
function buildPrompt(diff, prMeta) {
  const metaSection = prMeta.title
    ? `## PR Context
- **Title**: ${prMeta.title}
- **Author**: ${prMeta.author || "unknown"}
- **Branch**: \`${prMeta.headBranch}\` → \`${prMeta.baseBranch}\`
- **Changed files**: ${prMeta.changedFiles || "unknown"}
- **Lines**: +${prMeta.additions || 0} / -${prMeta.deletions || 0}
${prMeta.body ? `- **Description**: ${prMeta.body.slice(0, 500)}` : ""}
`
    : "";

  // Truncate diff if it's very large (>50KB)
  const MAX_DIFF_CHARS = 50000;
  const truncated = diff.length > MAX_DIFF_CHARS;
  const diffContent = truncated
    ? diff.slice(0, MAX_DIFF_CHARS) +
      "\n\n[... diff truncated for length ...]"
    : diff;

  return `You are an expert code reviewer. Analyze the following GitHub Pull Request diff and produce a structured review.

${metaSection}
## Diff

\`\`\`diff
${diffContent}
\`\`\`

## Your Task

Produce a structured Markdown review with EXACTLY these sections:

### 📋 Summary
Write 2–3 sentences summarizing what this PR does and why.

### ⚠️ Risks
A bullet-point list of potential issues, bugs, security concerns, or regressions. If none, write "No significant risks identified."

### 💡 Suggestions
A bullet-point list of actionable improvements (code quality, tests, documentation, patterns). Focus on what would make this code better.

### 🎯 Confidence Score
State your confidence in the analysis: **Low**, **Medium**, or **High**, followed by a brief one-sentence justification.
- Low: diff is large or context is unclear
- Medium: clear changes but some ambiguity
- High: small, well-scoped, well-described change

Be specific, technical, and constructive. Reference actual code from the diff when relevant.`;
}

// ─── Step 3: Call LLM ─────────────────────────────────────────────────────────
async function callAnthropic(prompt) {
  log(`Calling Anthropic (model: ${activeModel})...`);
  const res = await httpsPost(
    "api.anthropic.com",
    "/v1/messages",
    {
      "x-api-key": providerConfig.apiKey,
      "anthropic-version": "2023-06-01",
    },
    {
      model: activeModel,
      max_tokens: 2048,
      messages: [{ role: "user", content: prompt }],
    }
  );

  if (res.status !== 200) {
    throw new Error(
      `Anthropic API error ${res.status}: ${JSON.stringify(res.body).slice(0, 300)}`
    );
  }

  return res.body.content?.[0]?.text || "";
}

async function callGemini(prompt) {
  log(`Calling Gemini (model: ${activeModel})...`);
  const path = `/v1beta/models/${activeModel}:generateContent?key=${providerConfig.apiKey}`;
  const res = await httpsPost(
    "generativelanguage.googleapis.com",
    path,
    {},
    {
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: { maxOutputTokens: 2048, temperature: 0.2 },
    }
  );

  if (res.status !== 200) {
    throw new Error(
      `Gemini API error ${res.status}: ${JSON.stringify(res.body).slice(0, 300)}`
    );
  }

  return (
    res.body.candidates?.[0]?.content?.parts?.[0]?.text ||
    ""
  );
}

async function callGroq(prompt) {
  log(`Calling Groq (model: ${activeModel})...`);
  const res = await httpsPost(
    "api.groq.com",
    "/openai/v1/chat/completions",
    {
      Authorization: `Bearer ${providerConfig.apiKey}`,
    },
    {
      model: activeModel,
      messages: [{ role: "user", content: prompt }],
      max_tokens: 2048,
      temperature: 0.2,
    }
  );

  if (res.status !== 200) {
    throw new Error(
      `Groq API error ${res.status}: ${JSON.stringify(res.body).slice(0, 300)}`
    );
  }

  return res.body.choices?.[0]?.message?.content || "";
}

async function callLLM(prompt) {
  switch (provider) {
    case "anthropic":
      return callAnthropic(prompt);
    case "gemini":
      return callGemini(prompt);
    case "groq":
      return callGroq(prompt);
    default:
      throw new Error(`Unknown provider: ${provider}`);
  }
}

// ─── Step 4: Format output ───────────────────────────────────────────────────
function formatOutput(reviewText, prMeta, prUrl) {
  const timestamp = new Date().toISOString();
  const header = `> 🤖 **Automated PR Review** — Generated by [claude-review](https://github.com/pino12033/claude-builders-bounty/tree/main/bounties/issue-4-pr-reviewer) using \`${provider}/${activeModel}\`
> 📅 ${timestamp}
> 🔗 Reviewing: ${prUrl}

---

`;
  return header + reviewText;
}

// ─── Main ─────────────────────────────────────────────────────────────────────
async function main() {
  console.error(
    `🔍 Reviewing PR #${prNumber} in ${owner}/${repo} using ${provider}/${activeModel}...`
  );

  // 1. Fetch PR
  const { diff, prMeta } = await fetchPRData();
  if (!diff || diff.trim().length === 0) {
    console.error("⚠️  Warning: Diff is empty. PR may have no changes or be inaccessible.");
  }
  console.error(
    `📊 Diff size: ${(diff.length / 1024).toFixed(1)} KB | Files changed: ${prMeta.changedFiles || "?"}`
  );

  // 2. Build prompt
  const prompt = buildPrompt(diff, prMeta);
  log("Prompt length:", prompt.length, "chars");

  // 3. Call LLM
  console.error("🧠 Analyzing...");
  const reviewText = await callLLM(prompt);

  // 4. Format & output
  const output = formatOutput(reviewText, prMeta, prUrl);

  if (outputFormat === "json") {
    console.log(
      JSON.stringify(
        {
          pr: { url: prUrl, owner, repo, number: parseInt(prNumber) },
          provider,
          model: activeModel,
          meta: prMeta,
          review: reviewText,
          formattedReview: output,
          generatedAt: new Date().toISOString(),
        },
        null,
        2
      )
    );
  } else {
    console.log(output);
  }

  console.error("✅ Review complete.");
}

main().catch((err) => {
  console.error("❌ Fatal error:", err.message);
  if (verbose) console.error(err.stack);
  process.exit(1);
});
