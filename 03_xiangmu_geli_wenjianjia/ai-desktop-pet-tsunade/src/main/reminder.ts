/**
 * 定时提醒模块
 *
 * 基于 cron 表达式的提醒调度器。到时通过 IPC 向渲染进程发送提醒事件，
 * 并可选触发语音/文本吐槽（由渲染进程结合纲手人设播报）。
 */

import { app } from "electron";
import { EventEmitter } from "node:events";
import type { Reminder } from "../shared/ipc";

/** 简单 cron 字段匹配：支持 * /范围 逗号 单值 */
type CronField = { min: number; max: number; step?: number };

function parseCronField(expr: string, field: CronField): boolean {
  const now = new Date();
  const current =
    field.min === 0 ? now.getMinutes() : field.min === 1 ? now.getHours() : now.getDay();

  const parts = expr.split(",");
  for (const part of parts) {
    if (part === "*") return true;
    if (part.includes("/")) {
      const [base, stepStr] = part.split("/");
      const step = parseInt(stepStr, 10) || 1;
      const baseVal = base === "*" ? field.min : parseInt(base, 10);
      if ((current - baseVal) % step === 0) return true;
    } else if (part.includes("-")) {
      const [start, end] = part.split("-").map(Number);
      if (current >= start && current <= end) return true;
    } else {
      if (parseInt(part, 10) === current) return true;
    }
  }
  return false;
}

function _matchesCron(cron: string): boolean {
  // 格式：分钟 小时 日 月 周（简化，只支持前两位 + 周）
  const parts = cron.trim().split(/\s+/);
  if (parts.length < 2) return false;
  const minuteOk = parseCronField(parts[0], { min: 0, max: 59 });
  const hourOk = parseCronField(parts[1], { min: 0, max: 23 });
  const dayOfWeekOk =
    parts.length >= 5 ? parseCronField(parts[4], { min: 0, max: 6 }) : true;
  return minuteOk && hourOk && dayOfWeekOk;
}

interface ReminderState {
  timer: NodeJS.Timeout | null;
  reminders: Reminder[];
  enabled: boolean;
}

const state: ReminderState = {
  timer: null,
  reminders: [],
  enabled: false,
};

// 事件发射器，供 ipc 模块订阅并转发给渲染进程
export const reminderEmitter = new EventEmitter<{ fire: [Reminder] }>();

/** 获取当前分钟/小时下应触发的提醒 */
function checkDueReminders(): void {
  // 只在分钟变动时检查（避免高频轮询重复触发，这里按 60 秒轮询，依赖分钟级粒度）
  for (const reminder of state.reminders) {
    if (!reminder.enabled) continue;
    if (_matchesCron(reminder.cron)) {
      reminderEmitter.emit("fire", reminder);
    }
  }
}

/** 启动提醒调度器（每 60 秒检查一次） */
export function startReminderScheduler(intervalMs: number = 60000): void {
  if (state.timer) return;
  state.enabled = true;
  state.timer = setInterval(checkDueReminders, intervalMs);
  // 立即检查一次
  checkDueReminders();
}

/** 停止提醒调度器 */
export function stopReminderScheduler(): void {
  if (state.timer) {
    clearInterval(state.timer);
    state.timer = null;
  }
  state.enabled = false;
}

/** 设置提醒列表（由数据库/设置同步） */
export function setReminders(reminders: Reminder[]): void {
  state.reminders = reminders;
}

/** 获取提醒列表 */
export function getReminders(): Reminder[] {
  return [...state.reminders];
}

/** 应用退出时清理 */
app.on("before-quit", () => {
  stopReminderScheduler();
});
