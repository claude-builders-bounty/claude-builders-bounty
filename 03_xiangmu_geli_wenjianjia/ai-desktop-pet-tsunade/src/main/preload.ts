/**
 * 预加载脚本 (preload)
 *
 * 安全最佳实践：
 * 1. contextIsolation: true — 渲染进程与主进程上下文隔离
 * 2. nodeIntegration: false — 渲染进程禁用 Node.js
 * 3. 通过 contextBridge 暴露受控 API，渲染进程不可直接调用 require/electron
 * 4. 所有跨进程通信经 ipcMain 处理器校验
 */

import { contextBridge, ipcRenderer } from "electron";
import type {
  PetState,
  ChatMessage,
  SystemStats,
  Reminder,
  LlmConfig,
  AppSettings,
} from "../shared/ipc";
import { IPC_CHANNELS } from "../shared/ipc";
import type { PetApi } from "../shared/preload-types";

// 通用 IPC 调用：发送请求并等待响应
async function invoke<D = unknown>(channel: string, payload?: unknown): Promise<D> {
  try {
    const result = await ipcRenderer.invoke(channel, payload);
    return result as D;
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    throw new Error(`IPC 调用失败 [${channel}]: ${message}`);
  }
}

// 事件订阅：返回取消订阅函数
function on<T = unknown>(channel: string, callback: (data: T) => void): () => void {
  const handler = (_event: Electron.IpcRendererEvent, data: T) => callback(data);
  ipcRenderer.on(channel, handler);
  return () => {
    ipcRenderer.removeListener(channel, handler);
  };
}

// 暴露给渲染进程的受控 API
const api: PetApi = {
  // 窗口
  dragWindow: () => invoke(IPC_CHANNELS.WINDOW_DRAG),
  closeWindow: () => invoke(IPC_CHANNELS.WINDOW_CLOSE),
  minimizeWindow: () => invoke(IPC_CHANNELS.WINDOW_MINIMIZE),
  toggleDevTools: () => invoke(IPC_CHANNELS.WINDOW_TOGGLE_DEVTOOLS),
  setClickThrough: (enabled) => invoke(IPC_CHANNELS.WINDOW_SET_CLICK_THROUGH, enabled),
  setAlwaysOnTop: (enabled) => invoke(IPC_CHANNELS.WINDOW_SET_ALWAYS_ON_TOP, enabled),

  // 事件订阅（用于 chat:stream / monitor:stats / app:quit）
  on,

  // 宠物
  getPetState: () => invoke<PetState>(IPC_CHANNELS.PET_GET_STATE),
  setPetState: (state) => invoke(IPC_CHANNELS.PET_SET_STATE, state),
  setPetMood: (mood) => invoke(IPC_CHANNELS.PET_SET_MOOD, mood),
  playPetAnimation: (animation) => invoke(IPC_CHANNELS.PET_PLAY_ANIMATION, animation),

  // 聊天
  sendMessage: (content) =>
    invoke<{
      content: string;
      animation?: PetState["animation"];
      mood?: PetState["mood"];
    }>(IPC_CHANNELS.CHAT_SEND, { content }),
  getChatHistory: () => invoke<ChatMessage[]>(IPC_CHANNELS.CHAT_GET_HISTORY),
  clearChatHistory: () => invoke(IPC_CHANNELS.CHAT_CLEAR_HISTORY),
  onChatStream: (callback) => {
    const unsubscribe = on<IpcStreamChunk>(IPC_CHANNELS.CHAT_STREAM, (chunk) => {
      callback(chunk.text);
    });
    return unsubscribe;
  },

  // 设置
  getSettings: () => invoke<AppSettings>(IPC_CHANNELS.SETTINGS_GET),
  setSettings: (settings) => invoke(IPC_CHANNELS.SETTINGS_SET, settings),
  getLlmConfig: () => invoke<LlmConfig>(IPC_CHANNELS.SETTINGS_GET, { key: "llm" }),
  setLlmConfig: (config) => invoke(IPC_CHANNELS.SETTINGS_SET, { key: "llm", value: config }),

  // 系统监控
  startMonitor: () => invoke(IPC_CHANNELS.MONITOR_START),
  stopMonitor: () => invoke(IPC_CHANNELS.MONITOR_STOP),
  onSystemStats: (callback) => {
    const unsubscribe = on<SystemStats>(IPC_CHANNELS.MONITOR_STATS, (stats) => {
      callback(stats);
    });
    return unsubscribe;
  },

  // 提醒
  getReminders: () => invoke<Reminder[]>(IPC_CHANNELS.REMINDER_LIST),
  addReminder: (reminder) => invoke<Reminder>(IPC_CHANNELS.REMINDER_ADD, reminder),
  removeReminder: (id) => invoke(IPC_CHANNELS.REMINDER_REMOVE, id),
  toggleReminder: (id) => invoke(IPC_CHANNELS.REMINDER_TOGGLE, id),

  // 好感度
  getAffection: () => invoke<number>(IPC_CHANNELS.DB_GET_AFFECTION),
  setAffection: (value) => invoke(IPC_CHANNELS.DB_SET_AFFECTION, value),

  // 生命周期
  onQuit: (callback) => {
    const unsubscribe = on<void>("app:quit", () => callback());
    return unsubscribe;
  },
};

type IpcStreamChunk = { text: string };

contextBridge.exposeInMainWorld("__PET_API__", api);
