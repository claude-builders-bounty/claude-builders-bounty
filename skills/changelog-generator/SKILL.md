---
name: changelog-generator
description: Generate a structured CHANGELOG.md from git history. Use when the user asks to update, create, or regenerate a changelog, release notes, or version history from commits. Produces Keep a Changelog + Semantic Versioning output.
---

# Changelog Generator

Turn raw `git log` history into a structured, human-readable `CHANGELOG.md`
following [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) and
[Semantic Versioning](https://semver.org/).

## When to use

- The user asks to "update the changelog", "write release notes", or "summarize
  what changed since <tag>".
- Cutting a release and you need a version section.
- Auditing what landed between two refs.

## How it works

1. Determine the range. Default is the latest tag → `HEAD`. If no tags exist,
   the whole history is emitted under `[Unreleased]`.
2. Run the generator script:

   ```bash
   node scripts/generate-changelog.mjs [--from <ref>] [--to <ref>] [--output CHANGELOG.md] [--include-internal]
   ```

3. Review the generated block and commit it.

## Classification rules (Conventional Commits)

| Commit type                | Section         |
| -------------------------- | --------------- |
| `feat`                     | **Added**       |
| `fix`                      | **Fixed**       |
| `perf`, `refactor`         | **Changed**     |
| `docs`                     | **Documentation** |
| `revert`                   | **Removed**     |
| `chore`, `build`, `ci`, `test`, `style` | **Internal** (hidden unless `--include-internal`) |

A `!` after the type (`feat!:`) or a `BREAKING CHANGE:` footer marks the entry
as **breaking** (⚠️) and places it at the top of **Changed**.

## Idempotency

The generator writes its output between two sentinel markers:

```
<!-- changelog:generated:start -->
...generated content...
<!-- changelog:generated:end -->
```

Any hand-written preamble outside those markers is preserved on re-run.

## Script

See `scripts/generate-changelog.mjs`. Dependency-free, Node >= 18, ESM.

### scripts/generate-changelog.mjs

```js
#!/usr/bin/env node
// Dependency-free CHANGELOG generator (Node >= 18, ESM).
// Parses `git log` with control-char delimiters so multi-line bodies are safe.
import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync, existsSync } from "node:fs";

const US = "\x1f"; // field separator
const RS = "\x1e"; // record separator
const START = "<!-- changelog:generated:start -->";
const END = "<!-- changelog:generated:end -->";

function arg(name, fallback = undefined) {
  const i = process.argv.indexOf(`--${name}`);
  return i !== -1 && process.argv[i + 1] && !process.argv[i + 1].startsWith("--")
    ? process.argv[i + 1]
    : fallback;
}
const flag = (name) => process.argv.includes(`--${name}`);

function git(args) {
  return execFileSync("git", args, { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
}

function latestTag() {
  try {
    return git(["describe", "--tags", "--abbrev=0"]).trim();
  } catch {
    return null;
  }
}

function resolveRange() {
  const from = arg("from");
  const to = arg("to", "HEAD");
  if (from) return `${from}..${to}`;
  const tag = latestTag();
  return tag ? `${tag}..${to}` : to;
}

function readCommits(range) {
  const fmt = ["%H", "%h", "%s", "%b", "%an", "%aI"].join(US) + RS;
  const raw = git(["log", range, `--pretty=format:${fmt}`]);
  return raw
    .split(RS)
    .map((r) => r.replace(/^\n/, ""))
    .filter((r) => r.trim().length > 0)
    .map((record) => {
      const [hash, short, subject, body, author, date] = record.split(US);
      return { hash, short, subject: (subject || "").trim(), body: (body || "").trim(), author, date };
    });
}

const TYPE_MAP = {
  feat: "Added",
  fix: "Fixed",
  perf: "Changed",
  refactor: "Changed",
  docs: "Documentation",
  revert: "Removed",
  chore: "Internal",
  build: "Internal",
  ci: "Internal",
  test: "Internal",
  style: "Internal",
};

const SECTION_ORDER = ["Added", "Changed", "Fixed", "Removed", "Documentation", "Internal"];

function classify(commit) {
  // Conventional Commits: type(scope)!: subject
  const m = /^([a-zA-Z]+)(?:\(([^)]+)\))?(!)?:\s*(.*)$/.exec(commit.subject);
  const breaking =
    (m && m[3] === "!") || /(^|\n)BREAKING CHANGE:/.test(commit.body);

  let section = "Internal";
  let scope = null;
  let text = commit.subject;

  if (m) {
    const type = m[1].toLowerCase();
    scope = m[2] || null;
    text = m[4] || commit.subject;
    section = TYPE_MAP[type] || "Internal";
  }

  if (breaking) {
    section = "Changed";
    text = `⚠️ **BREAKING** ${text}`;
  }

  return { section, scope, text, breaking };
}

function buildSection(title, items) {
  if (items.length === 0) return "";
  const lines = items
    .sort((a, b) => a.text.localeCompare(b.text))
    .map((it) => {
      const scope = it.scope ? `**${it.scope}:** ` : "";
      return `- ${scope}${it.text} (\`${it.short}\`)`;
    });
  return `### ${title}\n\n${lines.join("\n")}\n`;
}

function generate() {
  const range = resolveRange();
  const commits = readCommits(range);
  const buckets = Object.fromEntries(SECTION_ORDER.map((s) => [s, []]));

  for (const c of commits) {
    const { section, scope, text } = classify(c);
    buckets[section].push({ short: c.short, scope, text });
  }

  const includeInternal = flag("include-internal");
  const sections = SECTION_ORDER.filter((s) => includeInternal || s !== "Internal")
    .map((s) => buildSection(s, buckets[s]))
    .filter(Boolean);

  const header = `## [Unreleased]\n\n_Generated from \`${range}\` on ${new Date().toISOString().slice(0, 10)}._\n`;
  const body = sections.length ? sections.join("\n") : "_No notable changes._\n";
  return `${header}\n${body}`;
}

function writeOut(content) {
  const out = arg("output", "CHANGELOG.md");
  const block = `${START}\n${content}\n${END}`;
  if (existsSync(out)) {
    const existing = readFileSync(out, "utf8");
    if (existing.includes(START) && existing.includes(END)) {
      const re = new RegExp(`${START}[\\s\\S]*?${END}`);
      writeFileSync(out, existing.replace(re, block));
      return out;
    }
    writeFileSync(out, `${existing.trimEnd()}\n\n${block}\n`);
    return out;
  }
  writeFileSync(out, `# Changelog\n\nAll notable changes to this project are documented here.\n\n${block}\n`);
  return out;
}

const path = writeOut(generate());
console.log(`Wrote ${path}`);
