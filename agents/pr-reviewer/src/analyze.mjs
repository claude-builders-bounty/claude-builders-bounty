/**
 * Pure analysis core for claude-review.
 * Takes GitHub PR metadata + file list, returns a structured review.
 * No network, no I/O — so it is fully testable.
 */

const SECRET_RX = /(api[_-]?key|secret|password|passwd|token|bearer)\s*[:=]\s*["'`]?[A-Za-z0-9_\-./+]{16,}/i;
const DEBUG_RX = /^\+.*\b(console\.(log|debug)|print\(|System\.out\.println|dd\(|var_dump\()/;
const TODO_RX = /^\+.*\b(TODO|FIXME|XXX|HACK)\b/;
const ESCAPE_RX = /^\+.*(@ts-ignore|@ts-expect-error|as any|: any\b|eslint-disable)/;
const EMPTY_CATCH_RX = /^\+.*catch\s*(\([^)]*\))?\s*\{\s*\}\s*;?\s*$/;
const LOCKFILES = /(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb?|poetry\.lock|Cargo\.lock|go\.sum|composer\.lock|Gemfile\.lock)$/i;
const MIGRATION = /(migrations?\/|\.sql$|schema\.|prisma\/)/i;
const CI = /(^|\/)\.github\/workflows\//;
const AUTH = /(auth|login|logout|session|oauth|jwt|permission|acl|rbac|passwd|password)/i;
const TESTFILE = /(^|\/)(tests?|__tests__|spec)(\/|$)|\.(test|spec)\.[cm]?[jt]sx?$|_test\.go$|test_.*\.py$/i;
const VERSION_FILE = /(^|\/)(package\.json|pyproject\.toml|Cargo\.toml|pubspec\.yaml|gemfile)$/i;

const big = (n) => n >= 400;
const huge = (n) => n >= 1000;

/** Collect patch-derived signals with a cap so a 50k-line diff stays cheap. */
function patchSignals(files, limit = 6000) {
  const sig = { secrets: [], debug: [], todos: [], escapes: [], emptyCatch: [], binary: [] };
  let seen = 0;
  for (const f of files) {
    if (!f.patch) {
      if (!f.additions && !f.deletions) sig.binary.push(f.filename);
      continue;
    }
    for (const line of f.patch.split("\n")) {
      if (line.startsWith("+++") || line.startsWith("---")) continue;
      if (seen++ > limit) break;
      if (line.startsWith("+")) {
        if (SECRET_RX.test(line) && !/process\.env|os\.environ|\$\{/.test(line)) sig.secrets.push(f.filename);
        if (DEBUG_RX.test(line)) sig.debug.push(f.filename);
        if (TODO_RX.test(line)) sig.todos.push(line.slice(1).trim());
        if (ESCAPE_RX.test(line)) sig.escapes.push(f.filename);
        if (EMPTY_CATCH_RX.test(line)) sig.emptyCatch.push(f.filename);
      }
    }
  }
  const uniq = (a) => [...new Set(a)];
  for (const k of Object.keys(sig)) sig[k] = uniq(sig[k]);
  return sig;
}

function summarize(meta, files, sig) {
  const n = files.length;
  const total = (meta.additions || 0) + (meta.deletions || 0);
  const areas = uniqAreas(files);
  const first = `This PR ${action(meta.title)} across ${n} file${n === 1 ? "" : "s"} (+${meta.additions}/-${meta.deletions}).`;
  const second = areas.length
    ? `It concentrates on ${areas.slice(0, 3).join(", ")}${areas.length > 3 ? ` and ${areas.length - 3} other area(s)` : ""}.`
    : "It has no clear area of concentration.";
  const touched = [];
  if (files.some((f) => TESTFILE.test(f.filename))) touched.push("tests are included");
  if (total >= 400) touched.push("the diff is large enough to need a careful pass");
  const third = (meta.body || "").trim().length < 40
    ? "The description is thin, so the intent has to be read from the diff."
    : "The description explains the intent.";
  return [first, second, third, touched.length ? `Note that ${touched.join(" and ")}.` : ""]
    .filter(Boolean)
    .join(" ");
}

function action(title = "") {
  const t = title.toLowerCase();
  if (/\b(fix|bug|patch|revert)\b/.test(t)) return "fixes a defect";
  if (/\b(add|feat|new|introduce|support)\b/.test(t)) return "adds functionality";
  if (/\b(refactor|cleanup|tidy|restructure|move)\b/.test(t)) return "refactors existing code";
  if (/\b(doc|readme|comment)\b/.test(t)) return "changes documentation";
  if (/\b(dep|bump|upgrade|chore|ci|build)\b/.test(t)) return "updates tooling or dependencies";
  if (/\b(remove|delete|drop)\b/.test(t)) return "removes code";
  return "changes code";
}

function uniqAreas(files) {
  const areas = new Set();
  for (const f of files) {
    const parts = f.filename.split("/");
    areas.add(parts.length === 1 ? parts[0] : parts.slice(0, 2).join("/"));
  }
  return [...areas];
}

function findRisks(meta, files, sig) {
  const risks = [];
  const total = (meta.additions || 0) + (meta.deletions || 0);
  const tests = files.filter((f) => TESTFILE.test(f.filename));
  const src = files.filter((f) => !TESTFILE.test(f.filename));

  if (files.some((f) => MIGRATION.test(f.filename)))
    risks.push("**Schema/data change** — migrations are hard to roll back; confirm the down-path exists.");
  if (files.some((f) => LOCKFILES.test(f.filename)))
    risks.push("**Lockfile committed** — verify it matches the manifest and has no surprise transitive bumps.");
  if (files.some((f) => CI.test(f.filename)))
    risks.push("**CI workflow change** — a broken workflow blocks every other PR.");
  if (files.some((f) => AUTH.test(f.filename)))
    risks.push("**Auth surface touched** — check the unauthenticated path, not just the happy flow.");
  if (sig.secrets.length)
    risks.push(`**Possible hardcoded credential** in \`${sig.secrets.slice(0, 3).join("`, `")}\` — check it is not a real key.`);
  if (src.length && !tests.length)
    risks.push("**No test files changed** — the new behaviour is unverified by the diff.");
  if (huge(total))
    risks.push(`**Very large diff** (${total} lines) — review fatigue makes real bugs slip through; consider splitting.`);
  else if (big(total))
    risks.push(`**Large diff** (${total} lines) — reserve review time.`);
  if (sig.emptyCatch.length)
    risks.push(`**Empty catch block** in \`${sig.emptyCatch[0]}\` — failures may be swallowed silently.`);
  if (files.some((f) => f.additions > 400))
    risks.push("**One file grows by 400+ lines** — a candidate for extraction.");
  if (meta.draft) risks.push("**Still a draft** — expect it to change before merge.");
  if (sig.escapes.length)
    risks.push(`**Type escape hatch used** (\`${sig.escapes[0]}\`) — the compiler guarantee is off there.`);
  if (files.some((f) => f.status === "removed"))
    risks.push("**File deletion** — check nothing still imports the removed path.");
  if (sig.binary.length)
    risks.push(`**Binary file(s) changed**: ${sig.binary.slice(0, 3).join(", ")} — reviewable only by eye.`);
  return risks;
}

function findSuggestions(meta, files, sig) {
  const out = [];
  const total = (meta.additions || 0) + (meta.deletions || 0);
  const tests = files.filter((f) => TESTFILE.test(f.filename));
  const src = files.filter((f) => !TESTFILE.test(f.filename));

  if (src.length && !tests.length)
    out.push("Add at least one test that fails before this change and passes after.");
  if ((meta.body || "").trim().length < 40)
    out.push("Expand the PR description: what changed, why, and how you verified it.");
  if (huge(total)) out.push("Split into stacked PRs if the pieces land independently.");
  if (sig.debug.length)
    out.push(`Drop or convert leftover debug output in \`${sig.debug[0]}\` (${sig.debug.length} file(s) affected).`);
  if (sig.todos.length)
    out.push(`Convert the added TODOs into linked issues (${sig.todos.length} found).`);
  if (!files.some((f) => VERSION_FILE.test(f.filename)) && /^(feat|fix)/i.test(meta.title || "") && !/^chore/i.test(meta.title || ""))
    out.push("If this is user-visible, make sure the version/changelog reflects it.");
  if (files.some((f) => f.status === "added") && files.some((f) => f.status === "removed"))
    out.push("A file was added and another removed — confirm that is a rename, not a duplicate.");
  return out;
}

function scoreConfidence(meta, files, risks) {
  const total = (meta.additions || 0) + (meta.deletions || 0);
  const hasTests = files.some((f) => TESTFILE.test(f.filename));
  const hasDesc = (meta.body || "").trim().length >= 40;
  let score = 0;
  score += huge(total) ? -2 : big(total) ? -1 : 1;
  score += hasTests ? 1 : -1;
  score += hasDesc ? 1 : -1;
  score += risks.length >= 4 ? -1 : 0;
  if (score >= 2) return "High";
  if (score <= -2) return "Low";
  return "Medium";
}

/** @returns {{summary: string, risks: string[], suggestions: string[], confidence: "Low"|"Medium"|"High"}} */
export function analyzePr(meta, files) {
  const sig = patchSignals(files);
  const risks = findRisks(meta, files, sig);
  const suggestions = findSuggestions(meta, files, sig);
  return { summary: summarize(meta, files, sig), risks, suggestions, confidence: scoreConfidence(meta, files, risks) };
}

export function renderMarkdown(meta, files, result, opts = {}) {
  const total = (meta.additions || 0) + (meta.deletions || 0);
  const L = [];
  L.push(`## Review: ${meta.title}`);
  L.push("");
  L.push(
    `\`${meta.user || "unknown"}\` · ${files.length} file(s) · +${meta.additions}/-${meta.deletions} (${total}) · confidence **${result.confidence}**`
  );
  L.push("");
  L.push("### Summary");
  L.push("");
  L.push(result.summary);
  L.push("");
  L.push("### Risks");
  L.push("");
  L.push(result.risks.length ? result.risks.map((r) => `- ${r}`).join("\n") : "- No structural risk detected.");
  L.push("");
  L.push("### Improvement suggestions");
  L.push("");
  L.push(result.suggestions.length ? result.suggestions.map((s) => `- ${s}`).join("\n") : "- Nothing notable.");
  L.push("");
  L.push("### Confidence");
  L.push("");
  L.push(
    `**${result.confidence}** — ${
      result.confidence === "High"
        ? "small, tested, well-described diff with few risk signals."
        : result.confidence === "Medium"
          ? "some risk signals or missing tests/description; a normal careful review."
          : "large, untested, or high-risk diff that needs real scrutiny."
    }`
  );
  L.push("");
  if (opts.footer !== false) {
    L.push("---");
    L.push("");
    L.push(
      `_Generated by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty) — heuristic pass over the diff. Not a substitute for a human read._`
    );
  }
  return L.join("\n");
}
