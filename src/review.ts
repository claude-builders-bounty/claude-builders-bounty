import { PRInfo } from "./github";

export interface ReviewOutput {
  summary: string;
  risks: string[];
  suggestions: string[];
  confidence: "Low" | "Medium" | "High";
  filesAnalyzed: number;
  model?: string;
}

interface ClaudeResponse {
  content: { type: string; text: string }[];
  stop_reason: string;
  model: string;
}

async function callClaude(
  pr: PRInfo,
  apiKey: string,
  model = "claude-sonnet-4-20250514",
  baseUrl = process.env.ANTHROPIC_BASE_URL || "https://api.anthropic.com"
): Promise<ReviewOutput> {
  const prompt = `You are a senior code reviewer. Analyze the following GitHub PR and produce a STRICT JSON review.

PR title: ${pr.title}
PR description: ${pr.body}
Files changed: ${pr.filesChanged.length}
Additions: ${pr.additions}, Deletions: ${pr.deletions}

Diff (truncated to 12000 chars):
\`\`\`diff
${pr.diff.slice(0, 12000)}
\`\`\`

Return ONLY valid JSON in this exact shape (no prose, no markdown fence):
{
  "summary": "<2-3 sentence overview of the change>",
  "risks": ["<risk 1>", "<risk 2>"],
  "suggestions": ["<suggestion 1>", "<suggestion 2>"],
  "confidence": "Low" | "Medium" | "High",
  "filesAnalyzed": ${pr.filesChanged.length}
}

Rules:
- summary <= 280 chars.
- risks: real, specific issues. Empty array if none.
- suggestions: actionable improvements. Empty array if none.
- confidence: Low if diff is huge (>10k chars) or unclear intent, Medium if normal, High if small and well-scoped.`;

  const resp = await fetch(`${baseUrl}/v1/messages`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model,
      max_tokens: 1024,
      messages: [{ role: "user", content: prompt }],
    }),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Claude API ${resp.status}: ${text.slice(0, 200)}`);
  }

  const data = (await resp.json()) as ClaudeResponse;
  const text = data.content.find((b) => b.type === "text")?.text ?? "";

  const cleaned = text.replace(/^```(?:json)?\s*/i, "").replace(/```\s*$/, "").trim();

  let parsed: any;
  try {
    parsed = JSON.parse(cleaned);
  } catch {
    return analyzePR(pr);
  }

  return {
    summary: String(parsed.summary ?? "").slice(0, 280),
    risks: Array.isArray(parsed.risks) ? parsed.risks.map(String) : [],
    suggestions: Array.isArray(parsed.suggestions) ? parsed.suggestions.map(String) : [],
    confidence: ["Low", "Medium", "High"].includes(parsed.confidence) ? parsed.confidence : "Medium",
    filesAnalyzed: pr.filesChanged.length,
    model: data.model ?? model,
  };
}

export function analyzePR(pr: PRInfo): ReviewOutput {
  // ── Risk patterns (25+, 5 categories) ────────────────────────────────────

  // 🔒 Security (14 patterns — incl. SQL injection & destructive ops)
  const securityPatterns: [RegExp, string][] = [
    [/password\s*=\s*["'][^"']+["']/i, "⚠️ Security: Hardcoded password detected"],
    [/secret\s*=\s*["'][^"']+["']/i, "⚠️ Security: Hardcoded secret detected"],
    [/api[_-]?key\s*=\s*["'][^"']+["']/i, "⚠️ Security: Hardcoded API key detected"],
    [/token\s*=\s*["'][^"']{10,}["']/i, "⚠️ Security: Hardcoded auth token detected"],
    [/eval\s*\(/i, "⚠️ Security: eval() usage — dynamic code execution risk"],
    [/new Function\s*\(/i, "⚠️ Security: new Function() — dynamic code execution risk"],
    [/exec\s*\(/i, "⚠️ Security: exec() usage — command injection risk"],
    [/innerHTML\s*=/i, "⚠️ Security: innerHTML assignment — XSS risk"],
    [/localStorage\.setItem\s*\(\s*["']token["']/i, "⚠️ Security: Token stored in localStorage"],
    [/process\.env\.\w+\s*\?\?\s*["'][^"']+["']/i, "⚠️ Security: Env fallback to hardcoded value"],
    [/\bDROP\s+(TABLE|DATABASE|INDEX|SCHEMA|VIEW|TRIGGER|PROCEDURE|FUNCTION|USER|ROLE)\b/i, "⚠️ Security: Destructive SQL DROP statement"],
    [/\bTRUNCATE\s+(TABLE)?\b/i, "⚠️ Security: Destructive SQL TRUNCATE statement"],
    [/\bWHERE\s+1\s*=\s*1\b/i, "⚠️ Security: SQL 'WHERE 1=1' pattern (often injection indicator)"],
    [/\bUNION\s+(ALL\s+)?SELECT\b/i, "⚠️ Security: SQL UNION SELECT — classic injection payload"],
    [/\b(OR|AND)\s+['"]?\w+['"]?\s*=\s*['"]?\w+['"]?/i, "⚠️ Security: SQL tautology pattern (e.g. OR 1=1) — possible injection"],
    [/--\s*$/m, "⚠️ Security: SQL comment marker (-- ) — possible injection attempt"],
  ];

  // 📐 Code Quality (8 patterns)
  const qualityPatterns: [RegExp, string][] = [
    [/TODO|FIXME|HACK|XXX/i, "📝 Code Quality: Unresolved code comment (TODO/FIXME/HACK)"],
    [/\bvar\s+\w+\s*=/i, "📝 Code Quality: Using 'var' instead of 'let'/'const'"],
    [/==\s*null|!=\s*null/i, "📝 Code Quality: Loose equality (use === instead)"],
    [/==\s*undefined|!=\s*undefined/i, "📝 Code Quality: Loose equality with undefined"],
    [/!is\s+\w+/i, "📝 Code Quality: Double negation (!is)"],
    [/\bdebugger\b/i, "📝 Code Quality: debugger statement left in code"],
    [/console\.(log|warn|error)\s*\(/i, "📝 Code Quality: console.log/warn/error in code"],
    [/\.then\(\s*\(\s*\)\s*=>/i, "📝 Code Quality: Missing .catch() on promise chain"],
  ];

  // ⚡ Performance (4 patterns)
  const perfPatterns: [RegExp, string][] = [
    [/for\s*\(\s*\w+\s+in\s+\w+\s*\)/i, "⚡ Performance: for...in loop (use Object.keys/values instead)"],
    [/\.forEach\s*\(/i, "⚡ Performance: forEach — consider for...of or .map()"],
  ];

  // 🐛 Bug patterns (3)
  const bugPatterns: [RegExp, string][] = [
    [/catch\s*\(\s*\w*\s*\)\s*\{\s*\}/i, "🐛 Bug: Empty catch block — errors silently swallowed"],
    [/\bnull\s*\.\w+/i, "🐛 Bug: Potential null reference access"],
    [/==\s*null|==\s*undefined/i, "🐛 Bug: Loose equality with null/undefined"],
  ];

  // 🧪 Test patterns
  const testPatterns: [RegExp, string][] = [
    [/skip\s*\(/i, "🧪 Test: .skip() used — test disabled"],
    [/xit\s*\(/i, "🧪 Test: xit() used — test disabled"],
  ];

  const allPatterns = [...securityPatterns, ...qualityPatterns, ...perfPatterns, ...bugPatterns, ...testPatterns];

  const { diff, additions, deletions, filesChanged, body } = pr;
  const risks: string[] = [];
  for (const [pattern, message] of allPatterns) {
    if (pattern.test(diff)) {
      risks.push(message);
    }
  }

  // Estimate complexity
  const totalChanges = additions + deletions;
  const complexity = totalChanges > 500 ? "large" : totalChanges > 100 ? "medium" : "small";

  // Confidence based on diff size
  let confidence: "Low" | "Medium" | "High" = "Medium";
  if (diff.length < 2000) confidence = "High";
  else if (diff.length > 50000) confidence = "Low";

  // Suggestions
  const suggestions: string[] = [];
  if (body.length < 20) suggestions.push("PR description is very brief — add more context");
  if (additions > 300) suggestions.push("Large PR — consider splitting into smaller changes");
  if (risks.some(r => r.includes("Security"))) suggestions.push("Security issues detected — review carefully before merging");
  if (!diff.includes("test")) suggestions.push("No test changes detected — consider adding tests");
  if (diff.includes("main") && !diff.includes("master")) suggestions.push("Direct main branch modification — use feature branches");
  if (!risks.some(r => r.includes("Test:"))) suggestions.push("No test coverage detected — consider adding tests");
  if (suggestions.length === 0) suggestions.push("Code looks reasonable — standard review practices apply.");

  return {
    summary: `${pr.title} modifies ${filesChanged.length} file(s) with ${additions} additions and ${deletions} deletions. This is a ${complexity} change.`,
    risks: risks.length > 0 ? risks : ["No obvious security risks detected in the diff."],
    suggestions,
    confidence,
    filesAnalyzed: filesChanged.length,
    model: "heuristic",
  };
}

export async function reviewPR(
  pr: PRInfo,
  opts: { apiKey?: string; model?: string; useHeuristic?: boolean; baseUrl?: string } = {}
): Promise<ReviewOutput> {
  if (opts.useHeuristic || !opts.apiKey) {
    return analyzePR(pr);
  }
  try {
    return await callClaude(pr, opts.apiKey, opts.model, opts.baseUrl);
  } catch (err) {
    console.error(`[claude-review] Claude call failed, falling back to heuristic: ${err instanceof Error ? err.message : err}`);
    return analyzePR(pr);
  }
}

export function formatMarkdown(pr: PRInfo, review: ReviewOutput): string {
  const safeTitle = pr.title.replace(/\|/g, "\\|");
  return `## 📋 PR Review: ${safeTitle}

### Summary
${review.summary}

### 🔍 Risks
${review.risks.map((r) => `- ${r}`).join("\n")}

### 💡 Suggestions
${review.suggestions.map((s) => `- ${s}`).join("\n")}

### ✅ Confidence Score: **${review.confidence}**

---
*Analyzed ${review.filesAnalyzed} file(s) | ${pr.additions} additions / ${pr.deletions} deletions | model: ${review.model ?? "heuristic"}*`;
}
