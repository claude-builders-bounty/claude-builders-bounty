import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(root, "../..");
const requireRealEvidence = process.argv.includes("--require-real-evidence");
const skipRemote = process.argv.includes("--skip-remote");
const submissionPrefix = "submissions/aviranchigoda/";

const checks = [];
const approvalGates = [];
const failures = [];

function record(name, status, evidence) {
  const entry = { name, status, evidence };

  if (status === "approval_gate") {
    approvalGates.push(entry);
  } else {
    checks.push(entry);
  }

  if (status === "failed") {
    failures.push(entry);
  }

  return entry;
}

function parseJsonFromOutput(output) {
  const trimmed = output.trim();
  const starts = [];

  for (let index = 0; index < trimmed.length; index += 1) {
    if (trimmed[index] === "{" || trimmed[index] === "[") {
      starts.push(index);
    }
  }

  for (const start of starts.reverse()) {
    try {
      return JSON.parse(trimmed.slice(start));
    } catch {
      // Some tools emit logs before JSON. Keep scanning for the last JSON object.
    }
  }

  return null;
}

function run(command, args, options = {}) {
  return new Promise((resolve) => {
    const child = spawn(command, args, {
      cwd: repoRoot,
      env: process.env,
      stdio: ["ignore", "pipe", "pipe"],
      ...options,
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("close", (code) => {
      resolve({ code, stdout, stderr });
    });
  });
}

async function githubApiJson(pathOrUrl) {
  const headers = {
    accept: "application/vnd.github+json",
    "user-agent": "n8n-weekly-dev-summary-pre-submit-audit",
  };
  const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN;

  if (token) {
    headers.authorization = `Bearer ${token}`;
  }

  const url = pathOrUrl.startsWith("https://")
    ? pathOrUrl
    : `https://api.github.com/${pathOrUrl.replace(/^\/+/, "")}`;
  const response = await fetch(url, { headers });

  if (response.ok) {
    return await response.json();
  }

  const ghPath = pathOrUrl.startsWith("https://api.github.com/")
    ? pathOrUrl.slice("https://api.github.com/".length)
    : pathOrUrl.replace(/^\/+/, "");
  const ghResult = await run("gh", ["api", ghPath]);

  if (ghResult.code === 0) {
    return JSON.parse(ghResult.stdout);
  }

  throw new Error(
    `GitHub API request failed with fetch ${response.status}; gh fallback exited ${ghResult.code}: ${(ghResult.stderr || ghResult.stdout).trim()}`,
  );
}

async function runPassingCommand(name, args) {
  const result = await run(process.execPath, args);

  if (result.code === 0) {
    record(name, "passed", "command exited 0");
    return result;
  }

  record(name, "failed", `command exited ${result.code}: ${(result.stderr || result.stdout).trim()}`);
  return result;
}

function envHasRealEvidenceInputs() {
  const anthropicApiKey = process.env.ANTHROPIC_API_KEY?.trim();
  const slackWebhookUrl = process.env.SLACK_WEBHOOK_URL?.trim();

  return Boolean(
    anthropicApiKey
      && slackWebhookUrl
      && !anthropicApiKey.includes("REPLACE_ME")
      && !slackWebhookUrl.includes("REPLACE_ME"),
  );
}

function walkFiles(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const fullPath = path.join(directory, entry.name);

    if (entry.isDirectory()) {
      return walkFiles(fullPath);
    }

    return fullPath;
  });
}

function secretScan() {
  const secretPattern = new RegExp([
    "sk-" + "ant-",
    "xox" + "[baprs]-",
    "gh" + "p_",
    "github" + "_pat_",
    "hooks" + "\\.slack\\.com\\/services\\/[A-Z0-9]+\\/[A-Z0-9]+\\/[A-Za-z0-9]+",
  ].join("|"));
  const matches = walkFiles(root)
    .filter((filePath) => !filePath.includes(`${path.sep}.git${path.sep}`))
    .flatMap((filePath) => {
      if (fs.statSync(filePath).isDirectory()) {
        return [];
      }

      const relativePath = path.relative(repoRoot, filePath);
      const contents = fs.readFileSync(filePath, "utf8");
      return secretPattern.test(contents) ? [relativePath] : [];
    });

  if (matches.length === 0) {
    record("secret scan", "passed", "no Anthropic, Slack, or GitHub token patterns found");
    return;
  }

  record("secret scan", "failed", `secret-like pattern found in: ${matches.join(", ")}`);
}

async function branchScopeCheck() {
  const commands = [
    ["git", ["-c", "core.fsmonitor=false", "diff", "--name-only", "origin/main...HEAD"]],
    ["git", ["-c", "core.fsmonitor=false", "diff", "--cached", "--name-only"]],
    ["git", ["-c", "core.fsmonitor=false", "diff", "--name-only"]],
  ];
  const files = new Set();

  for (const [command, args] of commands) {
    const result = await run(command, args);

    if (result.code !== 0) {
      record("branch scope", "failed", `failed to list changed files: ${(result.stderr || result.stdout).trim()}`);
      return;
    }

    result.stdout.split("\n").filter(Boolean).forEach((filePath) => files.add(filePath));
  }

  const outOfScope = [...files].filter((filePath) => !filePath.startsWith(submissionPrefix));

  if (outOfScope.length === 0) {
    record("branch scope", "passed", "all changed files are under submissions/aviranchigoda/");
    return;
  }

  record("branch scope", "failed", `out-of-scope changed files: ${outOfScope.join(", ")}`);
}

async function remoteIssueCheck() {
  if (skipRemote) {
    record("remote issue state", "skipped", "skipped by --skip-remote");
    return;
  }

  try {
    const [issue, search] = await Promise.all([
      githubApiJson("repos/claude-builders-bounty/claude-builders-bounty/issues/5"),
      githubApiJson("search/issues?q=repo:claude-builders-bounty/claude-builders-bounty+is:pr+is:open+%22weekly+dev+summary%22&per_page=1"),
    ]);

    if (issue.state !== "open") {
      record("remote issue state", "failed", `issue #5 is ${issue.state}`);
      return;
    }

    const competition = typeof search.total_count === "number"
      ? `${search.total_count} open matching PRs`
      : "unknown open PR count";

    record("remote issue state", "passed", `issue #5 is open; ${competition}`);
  } catch (error) {
    record("remote issue state", "failed", `GitHub status check failed: ${error.message}`);
  }
}

async function acceptanceChecks() {
  await runPassingCommand("check-acceptance syntax", ["--check", path.join(root, "check-acceptance.mjs")]);
  await runPassingCommand("mock validator syntax", ["--check", path.join(root, "validate-mock-execution.mjs")]);
  await runPassingCommand("real validator syntax", ["--check", path.join(root, "validate-real-execution.mjs")]);

  const localAcceptance = await run(process.execPath, [path.join(root, "check-acceptance.mjs"), "--no-write"]);
  const localAcceptanceJson = parseJsonFromOutput(localAcceptance.stdout);

  if (localAcceptance.code === 0 && localAcceptanceJson?.status === "passed") {
    record(
      "local acceptance",
      "passed",
      `${localAcceptanceJson.checks?.length ?? 0} checks passed; ${localAcceptanceJson.approvalGates?.length ?? 0} approval gates remain`,
    );
  } else {
    record("local acceptance", "failed", (localAcceptance.stderr || localAcceptance.stdout).trim());
  }

  await runPassingCommand("mock success no-write", [path.join(root, "validate-mock-execution.mjs"), "--no-write"]);
  await runPassingCommand("mock Slack failure no-write", [path.join(root, "validate-mock-execution.mjs"), "--expect-slack-failure", "--no-write"]);
  await runPassingCommand("real secret guard self-test", [path.join(root, "validate-real-execution.mjs"), "--self-test-secret-guard"]);
  await runPassingCommand("real input validation self-test", [path.join(root, "validate-real-execution.mjs"), "--self-test-input-validation"]);

  if (envHasRealEvidenceInputs()) {
    await runPassingCommand("real environment preflight", [path.join(root, "validate-real-execution.mjs"), "--check-env-only"]);
  } else {
    record(
      "real environment preflight",
      "approval_gate",
      "ANTHROPIC_API_KEY and SLACK_WEBHOOK_URL are required after user approval",
    );
  }

  const strictAcceptance = await run(process.execPath, [
    path.join(root, "check-acceptance.mjs"),
    "--require-real-evidence",
    "--no-write",
  ]);
  const strictJson = parseJsonFromOutput(strictAcceptance.stdout);

  if (strictAcceptance.code === 0 && strictJson?.status === "passed") {
    record("strict real evidence acceptance", "passed", "real evidence and screenshot are present");
  } else if (requireRealEvidence) {
    const strictFailureSummary = strictJson?.failures?.map((failure) => failure.name).join(", ")
      || (strictAcceptance.stderr || strictAcceptance.stdout).trim();
    record("strict real evidence acceptance", "failed", strictFailureSummary);
  } else {
    const gateSummary = strictJson?.failures?.map((failure) => failure.name).join(", ")
      || "real Anthropic/Slack execution evidence and real n8n screenshot are required";
    record("strict real evidence acceptance", "approval_gate", gateSummary);
  }
}

await remoteIssueCheck();
secretScan();
await branchScopeCheck();
await acceptanceChecks();

const status = failures.length > 0
  ? "failed"
  : approvalGates.length > 0
    ? "passed_with_approval_gates"
    : "passed";
const result = {
  status,
  generatedAt: new Date().toISOString(),
  requireRealEvidence,
  checks,
  approvalGates,
  failures,
};

console.log(JSON.stringify(result, null, 2));
process.exit(failures.length > 0 ? 1 : 0);
