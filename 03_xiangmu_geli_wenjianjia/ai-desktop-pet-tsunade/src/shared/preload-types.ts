/**
 * 预加载脚本暴露给渲染进程的 API 类型。
 * contextBridge 只能传递可序列化的值，函数通过 IPC 调用。
 */

import { AppSettings, PetState, ChatMessage, SystemStats, Reminder, LlmConfig } from "@shared/ipc";

/** 渲染进程可调用的 API */
export interface PetApi {
  // 窗口
  dragWindow: () => Promise<void>;
  closeWindow: () => Promise<void>;
  minimizeWindow: () => Promise<void>;
  toggleDevTools: () => Promise<void>;
  setClickThrough: (enabled: boolean) => Promise<void>;
  setAlwaysOnTop: (enabled: boolean) => Promise<void>;

  // 事件订阅（通用事件通道，如 chat:stream / monitor:stats / app:quit）
  on: <T = unknown>(channel: string, callback: (data: T) => void) => () => void;

  // 宠物
  getPetState: () => Promise<PetState>;
  setPetState: (state: Partial<PetState>) => Promise<void>;
  setPetMood: (mood: PetState["mood"]) => Promise<void>;
  playPetAnimation: (animation: PetState["animation"]) => Promise<void>;

  // 聊天
  sendMessage: (content: string) => Promise<{ content: string; animation?: PetState["animation"]; mood?: PetState["mood"] }>;
  getChatHistory: () => Promise<ChatMessage[]>;
  clearChatHistory: () => Promise<void>;
  onChatStream: (callback: (chunk: string) => void) => () => void;

  // 设置
  getSettings: () => Promise<AppSettings>;
  setSettings: (settings: Partial<AppSettings>) => Promise<void>;
  getLlmConfig: () => Promise<LlmConfig>;
  setLlmConfig: (config: Partial<LlmConfig>) => Promise<void>;

  // 系统监控
  startMonitor: () => Promise<void>;
  stopMonitor: () => Promise<void>;
  onSystemStats: (callback: (stats: SystemStats) => void) => () => void;

  // 提醒
  getReminders: () => Promise<Reminder[]>;
  addReminder: (reminder: Omit<Reminder, "id" | "createdAt">) => Promise<Reminder>;
  removeReminder: (id: string) => Promise<void>;
  toggleReminder: (id: string) => Promise<void>;

  // 好感度
  getAffection: () => Promise<number>;
  setAffection: (value: number) => Promise<void>;

  // 生命周期
  onQuit: (callback: () => void) => () => void;
}

/** 全局 window 对象扩展 */
declare global {
  interface Window {
    __PET_API__: PetApi;
  }
}

