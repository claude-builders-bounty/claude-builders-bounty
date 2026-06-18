#!/usr/bin/env node
/**
 * Smoke test: validate the review output against acceptance criteria.
 * Run: node test/smoke.mjs
 * Requires: OPENROUTER_API_KEY env var, GITHUB_TOKEN (optional)
 */

import { readFileSync } from "fs";
import { join } from "path";

const REQUIRED_SECTIONS = [
  "Summary of Changes",
  "Identified Risks",
  "Improvement Suggestions",
  "Confidence Score",
  "Overall Verdict"
];

async function test() {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    console.log("⚠️  OPENROUTER_API_KEY not set — skipping API test");
    return;
  }

  // Use our own PR #2879 as test subject
  const owner = "claude-builders-bounty";
  const repo = "claude-builders-bounty";
  const prNum = "2879";

  console.log(`🧪 Testing PR reviewer on ${owner}/${repo}#${prNum}...`);

  // Fetch PR diff
  const prResp = await fetch(`https://api.github.com/repos/${owner}/${repo}/pulls/${prNum}`);
  const prData = await prResp.json();
  const filesResp = await fetch(`https://api.github.com/repos/${owner}/${repo}/pulls/${prNum}/files`);
  const rawFiles = await filesResp.json();
  const filesData = Array.isArray(rawFiles) ? rawFiles : [];

  const diffText = filesData.filter(f => f.patch).map(f => f.patch).join("\n");
  if (!diffText) {
    console.log("❌ No diff available for this PR");
    process.exit(1);
  }

  // Build prompt
  const prompt = `You are a senior software engineer reviewing a GitHub Pull Request.

## PR Info
- **Title**: ${prData.title}
- **Description**: ${prData.body}
- **Stats**: +${prData.additions}/-${prData.deletions} | ${prData.changed_files} file(s) changed
- **Files**: ${filesData.map(f => f.filename).join(", ")}

## Diff
\`\`\`diff
${diffText}
\`\`\`

## Review Instructions
Provide a structured Markdown review comment with these sections:

### Summary of Changes (2-3 sentences)
Briefly describe what this PR does and why.

### Identified Risks
List potential issues (bugs, security, performance, breaking changes). If none, say "None identified."

### Improvement Suggestions
Code quality, readability, naming, error handling suggestions. Be constructive and specific.

### Confidence Score
Rate your confidence in this review:
- **High**: Clear changes, easy to evaluate
- **Medium**: Some ambiguity or complex logic
- **Low**: Very complex or unclear intent

### Overall Verdict
- ✅ **Approve** if changes look solid
- ⚠️ **Changes requested** if there are meaningful issues
- ℹ️ **Comment** if mostly fine but has minor notes

Be thorough but concise. Focus on what matters: correctness, security, maintainability.
`;

  // Call API
  const resp = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: process.env.CLAUDE_REVIEW_MODEL || "openai/gpt-oss-120b:free",
      messages: [{ role: "user", content: prompt }],
      max_tokens: 4096,
      temperature: 0.3
    })
  });

  if (!resp.ok) {
    const errText = await resp.text();
    console.log(`❌ API error ${resp.status}: ${errText}`);
    process.exit(1);
  }

  const data = await resp.json();
  const review = data?.choices?.[0]?.message?.content;
  if (!review) {
    console.log("❌ No review generated");
    process.exit(1);
  }

  // Validate sections
  console.log("\n📋 Review output:");
  console.log(review.substring(0, 500) + "...");
  console.log("\n✅ Validating sections...");

  let passed = 0;
  for (const section of REQUIRED_SECTIONS) {
    if (review.includes(section)) {
      console.log(`  ✅ ${section}`);
      passed++;
    } else {
      console.log(`  ❌ Missing: ${section}`);
    }
  }

  // Validate verdict
  const hasVerdict = review.includes("Approve") || review.includes("Changes requested") || review.includes("Comment");
  if (hasVerdict) {
    console.log("  ✅ Overall Verdict present");
    passed++;
  } else {
    console.log("  ❌ Overall Verdict missing");
  }

  // Validate confidence
  const hasConfidence = review.includes("High") || review.includes("Medium") || review.includes("Low");
  if (hasConfidence) {
    console.log("  ✅ Confidence Score present");
    passed++;
  } else {
    console.log("  ❌ Confidence Score missing");
  }

  const total = REQUIRED_SECTIONS.length + 2;
  console.log(`\n📊 Result: ${passed}/${total} checks passed`);
  if (passed === total) {
    console.log("🎉 All smoke tests passed!");
  } else {
    console.log("⚠️  Some checks failed");
  }
}

test().catch(err => {
  console.error("❌ Test error:", err.message);
  process.exit(1);
});
