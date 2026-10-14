import { getDb } from '@/lib/db';

export interface Item {
  id: number;
  title: string;
  created_at: number;
  archived_at: number | null;
}

export function listItems(): Item[] {
  return getDb()
    .prepare('SELECT id, title, created_at, archived_at FROM items WHERE archived_at IS NULL ORDER BY created_at DESC')
    .all() as Item[];
}

export function createItem(title: string): Item {
  const db = getDb();
  const now = Date.now();
  const insert = db.transaction((value: string) => {
    const info = db.prepare('INSERT INTO items (title, created_at) VALUES (?, ?)').run(value, now);
    return Number(info.lastInsertRowid);
  });
  const id = insert(title);
  return db.prepare('SELECT id, title, created_at, archived_at FROM items WHERE id = ?').get(id) as Item;
}
