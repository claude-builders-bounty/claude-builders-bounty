/**
 * Validates CLAUDE.md against reality. Run: node verify.mjs
 *
 * Checks three things:
 *   1. the doc has every section and section-content the bounty asks for
 *   2. every rule states a reason, and no unresolved placeholder is left
 *   3. every path the doc promises is actually created by scaffold.sh,
 *      every `npm run x` the doc tells Claude to run is a real script
 */

import { execFileSync } from "node:child_process";
import { existsSync, mkdtempSync, readdirSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const doc = readFileSync(join(HERE, "CLAUDE.md"), "utf8");

let fails = 0;
const check = (name, ok, detail = "") => {
  fails += ok ? 0 : 1;
  console.log(`${ok ? "OK  " : "FAIL"}  ${name}${ok || !detail ? "" : ` :: ${String(detail).slice(0, 80)}`}`);
};

/** recursively list files under a directory */
function* walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(full);
    else yield full;
  }
}

const noFences = doc.replace(/```[\s\S]*?```/g, "");
const SECTIONS = Object.fromEntries(
  noFences
    .split(/^## /m)
    .filter((c) => c.includes("\n"))
    .map((c) => {
      const nl = c.indexOf("\n");
      return [c.slice(0, nl).trim(), c.slice(nl + 1)];
    })
);
const section = (title) => SECTIONS[title] ?? "";

// ---- 1. required sections -------------------------------------------------------
for (const s of [
  "Stack",
  "Folder structure",
  "Dev commands",
  "Naming conventions",
  "Database rules",
  "Component patterns",
  "What we don't do, and why",
  "Definition of done",
]) {
  check(`section present: ${s}`, doc.includes(`## ${s}`));
}

const dbSec = section("Database rules");
const nameSec = section("Naming conventions");
const cmdSec = section("Dev commands");
check("covers DB migration rules", /migration/i.test(dbSec) && /_migrations/.test(doc));
check("covers project structure", />\s*Module|Folder structure/.test(doc));
check("covers naming conventions", nameSec.length > 200);
check("covers dev commands", /npm run dev/.test(doc) && /npm run test\b/.test(doc) && /npm run build/.test(doc));
check("covers patterns to follow", section("Component patterns").length > 400);
check("covers anti-patterns to avoid", section("What we don't do, and why").length > 400);

// ---- 2. every rule carries a reason --------------------------------------------
// join wrapped lines so a bullet's reason on the next line still counts
const bullets = [];
let cur = null;
for (const raw of noFences.split("\n")) {
  if (/^- /.test(raw)) {
    if (cur) bullets.push(cur);
    cur = raw.trim();
  } else if (cur && /^\s{2,}\S/.test(raw)) {
    cur += " " + raw.trim(); // continuation
  } else if (cur && !raw.trim()) {
    // blank line: the bullet may continue, keep it open
  } else if (cur) {
    bullets.push(cur);
    cur = null;
  }
}
if (cur) bullets.push(cur);

const ruleBullets = bullets.filter((l) => /^- (\*\*|`|[A-Z])/.test(l) && l.length > 30);
const noReason = ruleBullets.filter((l) => !/\bbecause\b/i.test(l));
check(`every rule bullet states a reason (${ruleBullets.length} bullets)`, noReason.length === 0, noReason[0]);

// anti-pattern table: every row's reason column must be substantive
const antiRows = section("What we don't do, and why")
  .split("\n")
  .filter((l) => /^\| .+ \| .+ \|$/.test(l.trim()))
  .filter((l) => !/^\|\s*-+/.test(l.trim()))
  .slice(1); // drop the header row
const thin = antiRows.filter((l) => (l.trim().split("|")[2] ?? "").trim().length < 15);
check(`anti-pattern rows each give a substantive reason (${antiRows.length} rows)`, thin.length === 0, thin[0]);
check("anti-pattern table is non-trivial", antiRows.length >= 12, `${antiRows.length} rows`);

// no unresolved placeholders outside code fences
for (const p of ["TODO", "FIXME", "XXX", "lorem", "your-app"]) {
  check(`no placeholder: ${p}`, !noFences.includes(p));
}
const ANGLED_OK = new Set(["entity", "feature"]);
const angledBad = [...noFences.matchAll(/<([a-z][a-z0-9_-]*)>/g)]
  .map((m) => m[1])
  .filter((n) => !ANGLED_OK.has(n));
check("no unknown <placeholder> outside code fences", angledBad.length === 0, angledBad.join(", "));

// ---- 3. the doc matches the scaffold -------------------------------------------
const tree = /## Folder structure\n\n```\n([\s\S]*?)```/.exec(doc)?.[1] ?? "";
check("folder-structure tree parsed", tree.length > 0);

/** resolve the indented tree into real relative paths */
const promised = [];
{
  const dirs = [];
  for (const raw of tree.split("\n")) {
    if (!raw.trim()) continue;
    const depth = Math.floor((raw.match(/^ */)?.[0].length ?? 0) / 2);
    const content = raw.trim().replace(/\s*#.*$/, "").trim();
    if (!content) continue;
    const isDir = content.endsWith("/");
    const name = content.replace(/\/+$/, "");
    dirs.length = depth;
    promised.push({ path: [...dirs, name].join("/"), isDir });
    if (isDir) dirs[depth] = name;
  }
}
check(`folder tree resolves to ${promised.length} paths`, promised.length > 10);

const tmp = mkdtempSync(join(tmpdir(), "claude-md-"));

/** find a bash that actually runs — on Windows `bash` may be the WSL launcher with no distro */
function findBash() {
  for (const c of [process.env.BASH, "bash", "C:/Program Files/Git/bin/bash.exe", "/usr/bin/bash"].filter(Boolean)) {
    try {
      execFileSync(c, ["-c", "exit 0"], { stdio: "pipe" });
      return c;
    } catch {
      /* next */
    }
  }
  return null;
}

try {
  const bash = findBash();
  check("a usable bash was found", bash !== null, "install git bash or WSL");
  execFileSync(bash, [join(HERE, "scaffold.sh"), join(tmp, "app")], { stdio: "pipe" });
  const root = join(tmp, "app");

  for (const { path, isDir } of promised) {
    // data/app.db is runtime-created: require its directory instead
    if (!isDir && path.endsWith(".db")) {
      check(`scaffold creates the dir for runtime file: ${path}`, existsSync(join(root, dirname(path))));
      continue;
    }
    check(`scaffold creates: ${path}`, existsSync(join(root, path)));
  }

  const refs = new Set(
    [...doc.matchAll(/`([a-z0-9().-]+\/[a-z0-9()./_-]+\.(?:ts|tsx|sql|json|yml|css))`/gi)].map((m) => m[1])
  );
  const missingRefs = [...refs].filter((r) => !existsSync(join(root, r)));
  check(`all ${refs.size} in-doc file references exist in the scaffold`, missingRefs.length === 0, missingRefs.join(", "));

  const scripts = Object.keys(JSON.parse(readFileSync(join(root, "package.json"), "utf8")).scripts ?? {});
  const invoked = [...new Set([...doc.matchAll(/npm run ([a-z0-9:_-]+)/g)].map((m) => m[1]))];
  const bogus = invoked.filter((s) => !scripts.includes(s));
  check(`all ${invoked.length} documented npm scripts exist`, bogus.length === 0, bogus.join(", "));

  check("migration runner matches the doc", /_migrations/.test(readFileSync(join(root, "db", "migrate.ts"), "utf8")));
  check("db handle sets WAL + foreign_keys", /journal_mode = WAL/.test(readFileSync(join(root, "db", "client.ts"), "utf8")));
  check("strict TS + noUncheckedIndexedAccess scaffolded", /noUncheckedIndexedAccess/.test(readFileSync(join(root, "tsconfig.json"), "utf8")));
  check("no ORM dependency present", !Object.keys(JSON.parse(readFileSync(join(root, "package.json"), "utf8")).dependencies ?? {}).some((d) => /prisma|drizzle|kysely|sequelize|typeorm/i.test(d)));
  check("better-sqlite3 is the database driver", /"better-sqlite3"/.test(readFileSync(join(root, "package.json"), "utf8")));
  check("db scripts load .env", /--env-file-if-exists=\.env/.test(readFileSync(join(root, "package.json"), "utf8")));
  check("runner wraps each migration in a transaction", /db\.transaction\(/.test(readFileSync(join(root, "db", "migrate.ts"), "utf8")));
  const badMigrations = [...walk(join(root, "db", "migrations"))].filter((f) => /^\s*(BEGIN|COMMIT)\s*;/im.test(readFileSync(f, "utf8")));
  check("migration files contain no BEGIN/COMMIT", badMigrations.length === 0, badMigrations.join(", "));
  check("scripts run through tsx, not bare node", /--import tsx/.test(readFileSync(join(root, "package.json"), "utf8")) && /"tsx"/.test(readFileSync(join(root, "package.json"), "utf8")));
  check("test script targets a .ts glob, not a directory", /tests\/unit\/\*\*\/\*\.test\.ts/.test(readFileSync(join(root, "package.json"), "utf8")));
  const todoFiles = [...walk(root)].filter((f) => /\.(ts|tsx|mjs|sql)$/.test(f) && /TODO|FIXME/.test(readFileSync(f, "utf8")));
  check("no TODO/FIXME left in scaffolded source", todoFiles.length === 0, todoFiles.join(", "));
} finally {
  rmSync(tmp, { recursive: true, force: true });
}

console.log("\n" + (fails === 0 ? "ALL PASS" : `${fails} FAILED`));
process.exit(fails ? 1 : 0);
