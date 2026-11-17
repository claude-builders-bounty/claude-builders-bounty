/**
 * 数据库模块（SQLite）
 *
 * 使用 sql.js（纯 JS SQLite，无需原生编译）存储：
 * - 对话历史
 * - 好感度
 * - 解锁的语音/动作/皮肤
 * - 提醒
 *
 * 数据库文件保存在用户数据目录下，避免写入应用安装目录。
 */

import { app } from "electron";
import path from "node:path";
import fs from "node:fs";
import initSqlJs from "sql.js";
import type { ChatMessage, Reminder, PetAnimation } from "../shared/ipc";

// sql.js 未附带 TypeScript 类型定义，使用本地占位类型，不影响运行时行为。
type Database = any;

/** 数据库文件路径 */
function getDbPath(): string {
  const userData = app.getPath("userData");
  const dbDir = path.join(userData, "data");
  if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true });
  }
  return path.join(dbDir, "pet.db");
}

let db: Database | null = null;
let dbReady: Promise<void> | null = null;

/** 初始化数据库并建表 */
export async function initDb(): Promise<Database> {
  if (db) return db;

  if (dbReady) {
    await dbReady;
    return db as Database;
  }

  dbReady = (async () => {
    const SQL = await initSqlJs();
    const filePath = getDbPath();
    const fileExists = fs.existsSync(filePath);

    let existingBuffer: Uint8Array | null = null;
    if (fileExists) {
      existingBuffer = fs.readFileSync(filePath);
    }

    db = new SQL.Database(existingBuffer);

    // 建表（幂等）
    db.exec(`
      PRAGMA journal_mode = WAL;

      CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp INTEGER NOT NULL,
        animation TEXT
      );

      CREATE TABLE IF NOT EXISTS affection (
        key TEXT PRIMARY KEY,
        value INTEGER NOT NULL DEFAULT 0,
        updated_at INTEGER NOT NULL
      );

      CREATE TABLE IF NOT EXISTS reminders (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        cron TEXT NOT NULL,
        enabled INTEGER NOT NULL DEFAULT 1,
        voice INTEGER NOT NULL DEFAULT 0,
        created_at INTEGER NOT NULL
      );

      CREATE TABLE IF NOT EXISTS unlocks (
        key TEXT PRIMARY KEY,
        unlocked_at INTEGER NOT NULL
      );

      CREATE INDEX IF NOT EXISTS idx_conversations_ts ON conversations(timestamp);
    `);

    // 如果是新建库，插入默认好感度
    const row = db
      .prepare("SELECT value FROM affection WHERE key = 'global'")
      .get() as { value: number } | undefined;
    if (!row) {
      db.prepare("INSERT INTO affection (key, value, updated_at) VALUES (?, ?, ?)").run(
        "global",
        50,
        Date.now()
      );
    }

    // 自动保存：每 30 秒将内存数据库写入磁盘
    setInterval(() => {
      saveDbToDisk();
    }, 30000);
  })();

  await dbReady;
  return db as Database;
}

/** 将内存数据库写入磁盘 */
export function saveDbToDisk(): void {
  if (!db) return;
  try {
    const data = db.export();
    const filePath = getDbPath();
    fs.writeFileSync(filePath, Buffer.from(data));
  } catch (err) {
    // 记录但不阻塞主流程
    console.error("[DB] 自动保存失败:", err);
  }
}

/** 应用退出时保存 */
app.on("before-quit", () => {
  saveDbToDisk();
});

/* ==================== 对话历史 ==================== */

/** 获取最近 N 条对话 */
export function getRecentConversations(limit: number = 50): ChatMessage[] {
  if (!db) throw new Error("数据库未初始化");
  const rows = db
    .prepare(
      "SELECT id, role, content, timestamp, animation FROM conversations ORDER BY timestamp DESC LIMIT ?"
    )
    .all(limit) as Array<{
      id: string;
      role: string;
      content: string;
      timestamp: number;
      animation: string | null;
    }>;

  return rows
    .reverse()
    .map((r) => ({
      id: r.id,
      role: r.role as "user" | "assistant" | "system",
      content: r.content,
      timestamp: r.timestamp,
      animation: (r.animation as PetAnimation | undefined) ?? undefined,
    }));
}

/** 保存一条消息 */
export function saveMessage(message: ChatMessage): void {
  if (!db) throw new Error("数据库未初始化");
  db.prepare(
    "INSERT OR REPLACE INTO conversations (id, role, content, timestamp, animation) VALUES (?, ?, ?, ?, ?)"
  ).run(
    message.id,
    message.role,
    message.content,
    message.timestamp,
    message.animation ?? null
  );
}

/** 清空对话历史 */
export function clearConversations(): void {
  if (!db) throw new Error("数据库未初始化");
  db.prepare("DELETE FROM conversations").run();
}

/* ==================== 好感度 ==================== */

export function getAffection(): number {
  if (!db) throw new Error("数据库未初始化");
  const row = db
    .prepare("SELECT value FROM affection WHERE key = 'global'")
    .get() as { value: number } | undefined;
  return row?.value ?? 50;
}

export function setAffection(value: number): void {
  if (!db) throw new Error("数据库未初始化");
  const clamped = Math.max(0, Math.min(100, value));
  db.prepare(
    "INSERT OR REPLACE INTO affection (key, value, updated_at) VALUES (?, ?, ?)"
  ).run("global", clamped, Date.now());
}

/** 原子性地对全局好感度做增量更新，避免并发读-改-写竞态导致更新丢失 */
export function adjustAffection(delta: number): void {
  if (!db) throw new Error("数据库未初始化");
  // SQLite 单条 UPDATE 是原子的，并发写入由数据库锁串行化，不会丢失更新
  db.prepare(
    "UPDATE affection SET value = MAX(0, MIN(100, value + ?)), updated_at = ? WHERE key = 'global'"
  ).run(delta, Date.now());
}

/* ==================== 提醒 ==================== */

export function getRemindersFromDb(): Reminder[] {
  if (!db) throw new Error("数据库未初始化");
  const rows = db
    .prepare(
      "SELECT id, title, content, cron, enabled, voice, created_at FROM reminders ORDER BY created_at DESC"
    )
    .all() as Array<{
      id: string;
      title: string;
      content: string;
      cron: string;
      enabled: number;
      voice: number;
      created_at: number;
    }>;

  return rows.map((r) => ({
    id: r.id,
    title: r.title,
    content: r.content,
    cron: r.cron,
    enabled: r.enabled === 1,
    voice: r.voice === 1,
    createdAt: r.created_at,
  }));
}

export function addReminderToDb(reminder: Reminder): void {
  if (!db) throw new Error("数据库未初始化");
  db.prepare(
    "INSERT OR REPLACE INTO reminders (id, title, content, cron, enabled, voice, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)"
  ).run(
    reminder.id,
    reminder.title,
    reminder.content,
    reminder.cron,
    reminder.enabled ? 1 : 0,
    reminder.voice ? 1 : 0,
    reminder.createdAt ?? Date.now()
  );
}

export function removeReminderFromDb(id: string): void {
  if (!db) throw new Error("数据库未初始化");
  db.prepare("DELETE FROM reminders WHERE id = ?").run(id);
}

export function toggleReminderInDb(id: string, enabled: boolean): void {
  if (!db) throw new Error("数据库未初始化");
  db.prepare("UPDATE reminders SET enabled = ? WHERE id = ?").run(enabled ? 1 : 0, id);
}

/* ==================== 解锁项目 ==================== */

export function isUnlocked(key: string): boolean {
  if (!db) return false;
  const row = db
    .prepare("SELECT 1 FROM unlocks WHERE key = ?")
    .get(key) as { 1: number } | undefined;
  return !!row;
}

export function unlock(key: string): void {
  if (!db) throw new Error("数据库未初始化");
  db.prepare("INSERT OR REPLACE INTO unlocks (key, unlocked_at) VALUES (?, ?)").run(
    key,
    Date.now()
  );
}

