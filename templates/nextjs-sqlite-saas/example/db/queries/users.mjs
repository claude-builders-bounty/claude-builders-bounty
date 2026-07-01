export function createUser(db, input) {
  db.prepare(`
    INSERT INTO users (id, email, name)
    VALUES (?, ?, ?)
  `).run(input.id, input.email, input.name);

  return findUserById(db, input.id);
}

export function findUserById(db, id) {
  return db.prepare(`
    SELECT id, email, name, created_at AS createdAt, updated_at AS updatedAt
    FROM users
    WHERE id = ? AND deleted_at IS NULL
  `).get(id) ?? null;
}

export function listUsers(db) {
  return db.prepare(`
    SELECT id, email, name, created_at AS createdAt
    FROM users
    WHERE deleted_at IS NULL
    ORDER BY created_at DESC, id DESC
  `).all();
}
