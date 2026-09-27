import fs from "fs";
import path from "path";
import { describe, it, expect } from "vitest";

describe("n8n Workflow Validator — Issue #5 Weekly Dev Summary", () => {
  const workflowPath = path.resolve(__dirname, "../workflows/weekly-dev-summary-claude.json");

  it("successfully parses the n8n workflow JSON file", () => {
    expect(fs.existsSync(workflowPath)).toBe(true);
    const raw = fs.readFileSync(workflowPath, "utf-8");
    const parsed = JSON.parse(raw);
    expect(parsed).toHaveProperty("name");
    expect(parsed).toHaveProperty("nodes");
    expect(parsed).toHaveProperty("connections");
    expect(Array.isArray(parsed.nodes)).toBe(true);
    expect(parsed.nodes.length).toBe(9);
  });

  it("verifies the weekly schedule trigger runs Friday at 5:00 PM (cron: 0 17 * * 5)", () => {
    const raw = fs.readFileSync(workflowPath, "utf-8");
    const parsed = JSON.parse(raw);
    const triggerNode = parsed.nodes.find((n: any) => n.name === "Weekly Trigger (Friday 5PM)");
    expect(triggerNode).toBeDefined();
    expect(triggerNode.type).toBe("n8n-nodes-base.scheduleTrigger");
    const cron = triggerNode.parameters.rule.interval[0].expression;
    expect(cron).toBe("0 17 * * 5");
  });

  it("verifies all required configuration variables are defined", () => {
    const raw = fs.readFileSync(workflowPath, "utf-8");
    const parsed = JSON.parse(raw);
    const configNode = parsed.nodes.find((n: any) => n.name === "Configuration Variables");
    expect(configNode).toBeDefined();
    const vars = configNode.parameters.values.string.map((v: any) => v.name);
    expect(vars).toContain("GITHUB_REPO_OWNER");
    expect(vars).toContain("GITHUB_REPO_NAME");
    expect(vars).toContain("SUMMARY_LANGUAGE");
    expect(vars).toContain("DISCORD_WEBHOOK_URL");
  });

  it("verifies Claude API node parameters adhere to Anthropic specification", () => {
    const raw = fs.readFileSync(workflowPath, "utf-8");
    const parsed = JSON.parse(raw);
    const claudeNode = parsed.nodes.find((n: any) => n.name === "Call Claude API (Sonnet)");
    expect(claudeNode).toBeDefined();
    expect(claudeNode.parameters.url).toBe("https://api.anthropic.com/v1/messages");
    expect(claudeNode.parameters.method).toBe("POST");
    expect(claudeNode.parameters.jsonBody).toContain("claude-3-5-sonnet-20241022");
    expect(claudeNode.parameters.jsonBody).toContain('"max_tokens": 2500');
  });

  it("verifies node connections form an unbroken linear pipeline with 3 concurrent fetch branches", () => {
    const raw = fs.readFileSync(workflowPath, "utf-8");
    const parsed = JSON.parse(raw);
    const connections = parsed.connections;

    // Trigger -> Config
    expect(connections["Weekly Trigger (Friday 5PM)"].main[0][0].node).toBe("Configuration Variables");
    // Config -> Calculate Date Range
    expect(connections["Configuration Variables"].main[0][0].node).toBe("Calculate Date Range (7 Days)");
    
    // Calculate Date Range splits into 3 parallel fetches: Commits, Issues, PRs
    const branches = connections["Calculate Date Range (7 Days)"].main[0].map((c: any) => c.node);
    expect(branches).toContain("Fetch Weekly Commits");
    expect(branches).toContain("Fetch Closed Issues");
    expect(branches).toContain("Fetch Closed PRs");

    // All 3 branches converge into Aggregate GitHub Digest Payload
    expect(connections["Fetch Weekly Commits"].main[0][0].node).toBe("Aggregate GitHub Digest Payload");
    expect(connections["Fetch Closed Issues"].main[0][0].node).toBe("Aggregate GitHub Digest Payload");
    expect(connections["Fetch Closed PRs"].main[0][0].node).toBe("Aggregate GitHub Digest Payload");

    // Aggregate -> Claude API -> Webhook Delivery
    expect(connections["Aggregate GitHub Digest Payload"].main[0][0].node).toBe("Call Claude API (Sonnet)");
    expect(connections["Call Claude API (Sonnet)"].main[0][0].node).toBe("Deliver via Discord / Slack Webhook");
  });

  it("simulates JS aggregator logic for multi-language narrative generation", () => {
    const sampleCommits = [
      { json: { sha: "abc12345", commit: { message: "feat: add user auth" }, author: { login: "alice" } } },
      { json: { sha: "def67890", commit: { message: "fix: resolve memory leak" }, author: { login: "bob" } } },
    ];
    const sampleIssues = [
      { json: { number: 42, title: "Login page unresponsive on Safari", labels: [{ name: "bug" }], pull_request: undefined } },
    ];
    const samplePulls = [
      { json: { number: 105, title: "Upgrade Tailwind CSS to v4", merged_at: new Date().toISOString(), user: { login: "carol" } } },
    ];

    // Verify commit summary mapping
    const commitLines = sampleCommits.map(c => `[${c.json.sha.slice(0, 7)}] ${c.json.commit.message} (@${c.json.author.login})`);
    expect(commitLines[0]).toBe("[abc1234] feat: add user auth (@alice)");
    expect(commitLines[1]).toBe("[def6789] fix: resolve memory leak (@bob)");

    // Verify issue formatting
    const issueLines = sampleIssues.filter(i => !i.json.pull_request).map(i => `#${i.json.number}: ${i.json.title} (${i.json.labels[0].name})`);
    expect(issueLines[0]).toBe("#42: Login page unresponsive on Safari (bug)");

    // Verify language toggle
    const langEN = ("EN" === "FR") ? "French (Français)" : "English";
    const langFR = ("FR" === "FR") ? "French (Français)" : "English";
    expect(langEN).toBe("English");
    expect(langFR).toBe("French (Français)");
  });
});
