#!/usr/bin/env node
import { createHash } from "node:crypto";
import { lstatSync, readdirSync, readFileSync, realpathSync, writeFileSync } from "node:fs";
import { basename, dirname, isAbsolute, join, relative, resolve } from "node:path";

function outsideFixture(root, path) {
  const target = join(realpathSync(dirname(resolve(path))), basename(path));
  const rel = relative(root, target);
  if (rel === "" || (!isAbsolute(rel) && rel !== ".." && !rel.startsWith("..\\") && !rel.startsWith("../"))) {
    throw new Error("Keep evidence files outside the fixture.");
  }
  return target;
}

function snapshot(root) {
  const entries = [];
  function walk(directory, prefix = "") {
    for (const name of readdirSync(directory).sort()) {
      const path = join(directory, name);
      const key = prefix ? `${prefix}/${name}` : name;
      const stat = lstatSync(path);
      if (stat.isSymbolicLink() || (!stat.isDirectory() && !stat.isFile())) {
        throw new Error(`Unsupported fixture entry: ${key}`);
      }
      const entry = { path: key, mode: stat.mode & 0o777, type: stat.isDirectory() ? "directory" : "file" };
      if (stat.isFile()) {
        const bytes = readFileSync(path);
        entry.bytes = bytes.length;
        entry.sha256 = createHash("sha256").update(bytes).digest("hex");
      }
      entries.push(entry);
      if (stat.isDirectory()) walk(path, key);
    }
  }
  walk(root);
  return { version: 1, root, entries };
}

try {
  const [command, fixture, baseline, after, ...extra] = process.argv.slice(2);
  if (!fixture || !baseline || extra.length || !["snapshot", "compare"].includes(command) ||
      (command === "compare") !== Boolean(after)) {
    throw new Error("Usage: fixture-integrity.mjs snapshot <fixture> <before.json> | compare <fixture> <before.json> <after.json>");
  }
  const root = realpathSync(fixture);
  if (!lstatSync(root).isDirectory()) throw new Error("Fixture must be a directory.");
  const beforePath = outsideFixture(root, baseline);
  const afterPath = after ? outsideFixture(root, after) : null;
  const previous = command === "compare" ? JSON.parse(readFileSync(beforePath, "utf8")) : null;
  if (previous && (previous.version !== 1 || previous.root !== root || !Array.isArray(previous.entries))) {
    throw new Error("Baseline must be a version 1 snapshot of this exact fixture.");
  }
  const current = snapshot(root);
  // Never overwrite the baseline or an earlier failed observation.
  writeFileSync(afterPath ?? beforePath, `${JSON.stringify(current, null, 2)}\n`, { flag: "wx" });
  if (command === "compare" && JSON.stringify(previous) !== JSON.stringify(current)) {
    throw new Error("Fixture changed; retain both manifests and do not claim a read-only pass.");
  }
  console.log(command === "compare" ? "Fixture content, modes and inventory match the baseline." : "Fixture baseline saved.");
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
