import assert from "node:assert/strict";
import { createUser } from "../db/queries/users.mjs";
import { createWorkspace } from "../db/queries/workspaces.mjs";
import { openDatabase } from "../db/client.mjs";
import { migrate } from "../db/migrate.mjs";

const db = openDatabase();
const applied = migrate(db);

assert.deepEqual(applied, ["0001_init.sql"]);

const foreignKeys = db.prepare("PRAGMA foreign_keys").get().foreign_keys;
assert.equal(foreignKeys, 1);

const user = createUser(db, {
  id: "usr_demo",
  email: "founder@example.com",
  name: "Demo Founder",
});

assert.match(user.createdAt, /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);

const workspace = createWorkspace(db, {
  id: "wsp_demo",
  ownerId: user.id,
  name: "Demo Workspace",
  slug: "demo-workspace",
});

assert.equal(workspace.ownerId, user.id);

let orphanRejected = false;
try {
  createWorkspace(db, {
    id: "wsp_orphan",
    ownerId: "missing_user",
    name: "Orphan Workspace",
    slug: "orphan-workspace",
  });
} catch {
  orphanRejected = true;
}
assert.equal(orphanRejected, true);

const membersBeforeDelete = db.prepare(`
  SELECT COUNT(*) AS count
  FROM workspace_members
  WHERE workspace_id = ?
`).get(workspace.id).count;

db.prepare("DELETE FROM users WHERE id = ?").run(user.id);

const membersAfterDelete = db.prepare(`
  SELECT COUNT(*) AS count
  FROM workspace_members
  WHERE workspace_id = ?
`).get(workspace.id).count;

assert.equal(membersBeforeDelete, 1);
assert.equal(membersAfterDelete, 0);

console.log("migrations applied: 0001_init.sql");
console.log("foreign_keys enabled: true");
console.log(`timestamp format: ${user.createdAt}`);
console.log("orphan workspace rejected: true");
console.log("ON DELETE CASCADE workspace_members: 1 -> 0");
console.log("validation: PASS");
