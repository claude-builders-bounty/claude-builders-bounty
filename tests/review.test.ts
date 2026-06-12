import { describe, it, expect } from "vitest";
import { analyzePR, formatMarkdown } from "../src/review";
import { PRInfo } from "../src/github";

describe("analyzePR", () => {
  const makePR = (overrides: Partial<PRInfo> = {}): PRInfo => ({
    owner: "test",
    repo: "test-repo",
    prNumber: 1,
    title: "Test PR",
    body: "This is a test PR with sufficient description.",
    diff: "const x = 1;\nconst y = 2;",
    filesChanged: ["src/index.ts"],
    additions: 10,
    deletions: 2,
    ...overrides,
  });

  it("returns High confidence for small diffs", () => {
    const pr = makePR({ diff: "small diff", additions: 5, deletions: 1 });
    const result = analyzePR(pr);
    expect(result.confidence).toBe("High");
  });

  it("returns Low confidence for large diffs", () => {
    const pr = makePR({ diff: "x".repeat(60000), additions: 30000, deletions: 100 });
    const result = analyzePR(pr);
    expect(result.confidence).toBe("Low");
  });

  it("detects hardcoded credentials", () => {
    const pr = makePR({ diff: "const token = 'sk-12345';\nconst password = 'secret';" });
    const result = analyzePR(pr);
    // Should match at least one of: password, secret, token, api key
    expect(result.risks.some(r => /password|secret|token|api key|credential/i.test(r))).toBeTruthy();
  });

  it("detects destructive database operations", () => {
    const pr = makePR({ diff: "DROP TABLE users;" });
    const result = analyzePR(pr);
    expect(result.risks.some(r => /destructive/i.test(r))).toBeTruthy();
  });

  it("detects dynamic code execution", () => {
    const pr = makePR({ diff: "eval('console.log(1)')" });
    const result = analyzePR(pr);
    expect(result.risks.some(r => /dynamic code execution/i.test(r))).toBeTruthy();
  });

  it("suggests tests when none detected", () => {
    const pr = makePR({ diff: "function add(a: number, b: number) { return a + b; }" });
    const result = analyzePR(pr);
    expect(result.suggestions.some(s => /test/i.test(s))).toBeTruthy();
  });

  it("includes all required output fields", () => {
    const pr = makePR();
    const result = analyzePR(pr);
    expect(result).toHaveProperty("summary");
    expect(result).toHaveProperty("risks");
    expect(result).toHaveProperty("suggestions");
    expect(result).toHaveProperty("confidence");
    expect(result).toHaveProperty("filesAnalyzed");
    expect(["Low", "Medium", "High"]).toContain(result.confidence);
  });
});

describe("formatMarkdown", () => {
  it("outputs structured markdown with all sections", () => {
    const pr: PRInfo = {
      owner: "owner",
      repo: "repo",
      prNumber: 123,
      title: "Add new feature",
      body: "Adds a new feature",
      diff: "console.log('hello');",
      filesChanged: ["src/feature.ts"],
      additions: 50,
      deletions: 10,
    };
    const review = analyzePR(pr);
    const output = formatMarkdown(pr, review);

    expect(output).toContain("## 📋 PR Review:");
    expect(output).toContain("### Summary");
    expect(output).toContain("### 🔍 Risks");
    expect(output).toContain("### 💡 Suggestions");
    expect(output).toContain("### ✅ Confidence Score:");
    expect(output).toContain("Add new feature modifies");
  });

  it("includes file count and diff stats", () => {
    const pr: PRInfo = {
      owner: "owner",
      repo: "repo",
      prNumber: 1,
      title: "Fix bug",
      body: "Fixes a bug",
      diff: "const x = 1;",
      filesChanged: ["a.ts", "b.ts", "c.ts"],
      additions: 100,
      deletions: 20,
    };
    const review = analyzePR(pr);
    const output = formatMarkdown(pr, review);
    expect(output).toContain("3 file(s)");
    expect(output).toContain("100 additions");
    expect(output).toContain("20 deletions");
  });
});