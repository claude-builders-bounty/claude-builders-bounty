export function createWorkspace(db, input) {
  db.exec("BEGIN");
  try {
    db.prepare(`
      INSERT INTO workspaces (id, owner_id, name, slug)
      VALUES (?, ?, ?, ?)
    `).run(input.id, input.ownerId, input.name, input.slug);

    db.prepare(`
      INSERT INTO workspace_members (workspace_id, user_id, role)
      VALUES (?, ?, 'owner')
    `).run(input.id, input.ownerId);

    const workspace = findWorkspaceById(db, input.id);
    db.exec("COMMIT");
    return workspace;
  } catch (error) {
    db.exec("ROLLBACK");
    throw error;
  }
}

export function findWorkspaceById(db, id) {
  return db.prepare(`
    SELECT id, owner_id AS ownerId, name, slug, created_at AS createdAt
    FROM workspaces
    WHERE id = ?
  `).get(id) ?? null;
}
