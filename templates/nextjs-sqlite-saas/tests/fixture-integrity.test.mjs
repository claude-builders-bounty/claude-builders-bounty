import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { chmodSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const script = resolve(dirname(fileURLToPath(import.meta.url)), "../verification/fixture-integrity.mjs");

function fixture(t) {
  const tempParent = realpathSync(tmpdir());
  const root = mkdtempSync(join(tempParent, "nextjs-fixture-integrity-"));
  t.after(() => {
    assert.equal(dirname(realpathSync(root)), tempParent);
    rmSync(root, { recursive: true, force: true });
  });
  const project = join(root, "app");
  mkdirSync(project);
  writeFileSync(join(project, "package.json"), '{"private":true}\n');
  writeFileSync(join(project, ".gitignore"), "ignored.txt\n");
  const before = join(root, "before.json");
  const after = join(root, "after.json");
  const run = (...args) => spawnSync(process.execPath, [script, ...args], { encoding: "utf8" });
  const initial = run("snapshot", project, before);
  assert.equal(initial.status, 0, initial.stderr);
  return { root, project, before, after, run };
}

test("a no-git fixture compares unchanged without touching the baseline", (t) => {
  const f = fixture(t);
  const original = readFileSync(f.before, "utf8");
  const result = f.run("compare", f.project, f.before, f.after);
  assert.equal(result.status, 0, result.stderr);
  assert.equal(readFileSync(f.before, "utf8"), original);
  assert.equal(readFileSync(f.after, "utf8"), original);
});

for (const [name, change] of [
  ["same-size content edit", (p) => writeFileSync(join(p, "package.json"), '{"private":null}\n')],
  ["file deletion", (p) => rmSync(join(p, "package.json"))],
  ["git-ignored addition", (p) => writeFileSync(join(p, "ignored.txt"), "added")],
  ["empty directory addition", (p) => mkdirSync(join(p, "new-empty-directory"))],
]) {
  test(`rejects ${name} and preserves the failed observation`, (t) => {
    const f = fixture(t);
    change(f.project);
    const result = f.run("compare", f.project, f.before, f.after);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /Fixture changed/);
    assert.notEqual(readFileSync(f.after, "utf8"), readFileSync(f.before, "utf8"));
  });
}

test("does not overwrite an existing baseline or observation", (t) => {
  const f = fixture(t);
  const original = readFileSync(f.before, "utf8");
  assert.equal(f.run("snapshot", f.project, f.before).status, 1);
  assert.equal(f.run("compare", f.project, f.before, f.before).status, 1);
  assert.equal(readFileSync(f.before, "utf8"), original);
});

test("rejects evidence inside the fixture and baselines from another fixture", (t) => {
  const f = fixture(t);
  assert.equal(f.run("snapshot", f.project, join(f.project, "before.json")).status, 1);
  const other = join(f.root, "other");
  mkdirSync(other);
  assert.equal(f.run("compare", other, f.before, f.after).status, 1);
});

test("rejects symlinked fixture entries instead of reading outside the fixture", (t) => {
  const f = fixture(t);
  // Windows directory junctions do not require symlink privilege.
  symlinkSync(f.root, join(f.project, "escape"), process.platform === "win32" ? "junction" : "dir");
  const result = f.run("compare", f.project, f.before, f.after);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /Unsupported fixture entry/);
});

test("detects permission changes on POSIX", { skip: process.platform === "win32" }, (t) => {
  const f = fixture(t);
  chmodSync(join(f.project, "package.json"), 0o700);
  assert.equal(f.run("compare", f.project, f.before, f.after).status, 1);
});
