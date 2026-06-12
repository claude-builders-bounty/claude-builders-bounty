import { describe, it, expect } from "vitest";
import { analyzePR, formatMarkdown } from "../src/review";
import { PRInfo } from "../src/github";

const makePR = (overrides: Partial<PRInfo> = {}): PRInfo => ({
  owner: "test",
  repo: "test-repo",
  prNumber: 1,
  title: "Test PR",
  body: "This is a test PR with sufficient description for proper review context.",
  diff: "const x = 1;\nconst y = 2;",
  filesChanged: ["src/index.ts"],
  additions: 10,
  deletions: 2,
  ...overrides,
});

describe("analyzePR — edge cases (v1.1.0)", () => {
  it("handles empty diff gracefully", () => {
    const pr = makePR({ diff: "", additions: 0, deletions: 0, filesChanged: [] });
    const result = analyzePR(pr);
    expect(result.confidence).toBe("High");
    expect(result.filesAnalyzed).toBe(0);
    // Empty diff → no real risks → explicit fallback message
    expect(result.risks).toEqual(["No obvious security risks detected in the diff."]);
  });

  it("detects SQL DROP TABLE as destructive", () => {
    const pr = makePR({ diff: "DROP TABLE users;" });
    const result = analyzePR(pr);
    expect(result.risks).toContain("⚠️ Security: Destructive SQL DROP statement");
  });

  it("detects SQL OR/AND tautology injection (e.g. OR 1=1)", () => {
    const pr = makePR({ diff: "SELECT * FROM users WHERE id = 1 OR 1=1;" });
    const result = analyzePR(pr);
    expect(result.risks).toContain("⚠️ Security: SQL tautology pattern (e.g. OR 1=1) — possible injection");
  });

  it("detects SQL TRUNCATE", () => {
    const pr = makePR({ diff: "TRUNCATE TABLE logs;" });
    const result = analyzePR(pr);
    expect(result.risks).toContain("⚠️ Security: Destructive SQL TRUNCATE statement");
  });

  it("handles unicode in diff without crashing", () => {
    const pr = makePR({
      diff: "// 中文注释\nconst greeting = '你好世界';\nlet emoji = '🚀';\n",
      additions: 3,
      deletions: 0,
      filesChanged: ["i18n/zh.ts", "constants/greetings.ts", "ui/Emoji.tsx"],
    });
    const result = analyzePR(pr);
    expect(result.summary).toContain("3 file");
    expect(result.confidence).toBe("High");
  });

  it("flags huge PRs as Low confidence with split suggestion", () => {
    const pr = makePR({
      diff: "x".repeat(60000),
      additions: 30000,
      deletions: 5000,
      filesChanged: Array.from({ length: 50 }, (_, i) => `file${i}.ts`),
    });
    const result = analyzePR(pr);
    expect(result.confidence).toBe("Low");
    expect(result.suggestions.some(s => /splitting/i.test(s))).toBeTruthy();
  });
});

describe("analyzePR — null/undefined safety (v1.1.0)", () => {
  it("handles missing diff/body/files fields gracefully (GitHub API oddities)", () => {
    // Type says required, but real Octokit can return undefined for empty/draft PRs
    const pr: any = {
      owner: "x",
      repo: "y",
      prNumber: 1,
      title: "Bare bones PR",
      // diff, body, filesChanged, additions, deletions all missing
    };
    expect(() => analyzePR(pr)).not.toThrow();
    const result = analyzePR(pr);
    expect(result.filesAnalyzed).toBe(0);
    expect(result.risks).toEqual(["No obvious security risks detected in the diff."]);
  });
});

describe("analyzePR — boundary conditions (v1.1.0)", () => {
  it("exactly 2000 chars diff → Medium (not High)", () => {
    const pr = makePR({ diff: "x".repeat(2000) });
    expect(analyzePR(pr).confidence).toBe("Medium");
  });

  it("exactly 50000 chars diff → Medium (not Low)", () => {
    const pr = makePR({ diff: "x".repeat(50000) });
    expect(analyzePR(pr).confidence).toBe("Medium");
  });

  it("1999 chars diff → High", () => {
    const pr = makePR({ diff: "x".repeat(1999) });
    expect(analyzePR(pr).confidence).toBe("High");
  });

  it("50001 chars diff → Low", () => {
    const pr = makePR({ diff: "x".repeat(50001) });
    expect(analyzePR(pr).confidence).toBe("Low");
  });
});

describe("formatMarkdown — edge cases (v1.1.0)", () => {
  it("escapes pipe characters in title to not break Markdown table rendering", () => {
    const pr = makePR({ title: "Fix | pipe | in title" });
    const review = analyzePR(pr);
    const output = formatMarkdown(pr, review);
    // Pipe characters in title must be escaped so they don't break Markdown table syntax
    expect(output).toContain("Fix \\| pipe \\| in title");
    expect(output).not.toMatch(/## 📋 PR Review: Fix \|/); // raw pipes in header would break tables
  });

  it("renders correctly with zero changes", () => {
    const pr = makePR({ diff: "", additions: 0, deletions: 0, filesChanged: [] });
    const review = analyzePR(pr);
    const output = formatMarkdown(pr, review);
    expect(output).toContain("0 additions / 0 deletions");
  });
});
