/**
 * 共享 IPC 通道定义与类型
 * 主进程与渲染进程通过 preload 脚本的 contextBridge 通信，
 * 所有通道名统一定义在此，避免字符串拼写错误。
 */

/** 所有 IPC 通道名 */
export const IPC_CHANNELS = {
  // 窗口控制
  WINDOW_DRAG: "window:drag",
  WINDOW_CLOSE: "window:close",
  WINDOW_MINIMIZE: "window:minimize",
  WINDOW_TOGGLE_DEVTOOLS: "window:toggle-devtools",
  WINDOW_SET_CLICK_THROUGH: "window:set-click-through",
  WINDOW_SET_ALWAYS_ON_TOP: "window:set-always-on-top",

  // 宠物状态
  PET_GET_STATE: "pet:get-state",
  PET_SET_STATE: "pet:set-state",
  PET_SET_MOOD: "pet:set-mood",
  PET_PLAY_ANIMATION: "pet:play-animation",
  PET_TOGGLE_CLICK_THROUGH: "pet:toggle-click-through",

  // 聊天
  CHAT_SEND: "chat:send",
  CHAT_GET_HISTORY: "chat:get-history",
  CHAT_CLEAR_HISTORY: "chat:clear-history",
  CHAT_STREAM: "chat:stream",

  // 设置
  SETTINGS_GET: "settings:get",
  SETTINGS_SET: "settings:set",
  SETTINGS_GET_ALL: "settings:get-all",
  SETTINGS_SET_ALL: "settings:set-all",

  // 系统监控
  MONITOR_START: "monitor:start",
  MONITOR_STOP: "monitor:stop",
  MONITOR_STATS: "monitor:stats",

  // 提醒
  REMINDER_LIST: "reminder:list",
  REMINDER_ADD: "reminder:add",
  REMINDER_REMOVE: "reminder:remove",
  REMINDER_TOGGLE: "reminder:toggle",

  // 数据库
  DB_GET_CONVERSATIONS: "db:get-conversations",
  DB_GET_AFFECTION: "db:get-affection",
  DB_SET_AFFECTION: "db:set-affection",
} as const;

/** 通道名联合类型 */
export type IpChannel = (typeof IPC_CHANNELS)[keyof typeof IPC_CHANNELS];

/** 宠物心情 */
export type PetMood = "happy" | "angry" | "drunk" | "tired" | "love" | "normal";

/** 宠物动作类型 */
export type PetAnimation =
  | "idle"
  | "talk"
  | "drink"
  | "gamble"
  | "angry"
  | "heal"
  | "blush"
  | "sulk";

/** 宠物运行状态 */
export interface PetState {
  visible: boolean;
  x: number;
  y: number;
  scale: number;
  mood: PetMood;
  animation: PetAnimation;
  clickThrough: boolean;
  alwaysOnTop: boolean;
  volume: number;
  affection: number; // 0-100 好感度
}

/** LLM 提供商 */
export type LlmProvider = "openai" | "anthropic" | "ollama";

/** LLM 配置 */
export interface LlmConfig {
  provider: LlmProvider;
  apiKey: string;
  baseUrl: string;
  model: string;
  temperature: number;
  maxTokens: number;
  systemPrompt: string;
}

/** 应用设置 */
export interface AppSettings {
  llm: LlmConfig;
  showMonitor: boolean;
  monitorInterval: number; // ms
  reminders: Reminder[];
  clickThrough: boolean;
  alwaysOnTop: boolean;
  autoStart: boolean;
  language: "zh-CN" | "en-US";
}

/** 提醒 */
export interface Reminder {
  id: string;
  title: string;
  content: string;
  cron: string; // cron 表达式
  enabled: boolean;
  voice: boolean; // 是否语音播报
  createdAt: number;
}

/** 聊天消息 */
export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
  animation?: PetAnimation; // 助手回复时建议的动作
  mood?: PetMood; // 助手回复时的心情
}

/** 系统监控数据 */
export interface SystemStats {
  cpu: number; // 0-100
  memory: { total: number; used: number; free: number; percent: number };
  network: { up: number; down: number }; // bytes/s
  timestamp: number;
}

/** IPC 请求/响应泛型 */
export interface IpcRequest<Payload = unknown> {
  channel: IpChannel;
  payload: Payload;
  id: string;
}

export interface IpcResponse<Data = unknown> {
  id: string;
  success: boolean;
  data?: Data;
  error?: string;
}

/** LLM 聊天请求 */
export interface LlmChatRequest {
  messages: Array<{ role: "user" | "assistant" | "system"; content: string }>;
  temperature?: number;
  maxTokens?: number;
  stream?: boolean;
}

/** LLM 聊天响应 */
export interface LlmChatResponse {
  content: string;
  animation?: PetAnimation;
  mood?: PetMood;
}

/** 错误码 */
export const ERROR_CODES = {
  LLM_API_ERROR: "LLM_API_ERROR",
  LLM_INVALID_CONFIG: "LLM_INVALID_CONFIG",
  DB_ERROR: "DB_ERROR",
  WINDOW_ERROR: "WINDOW_ERROR",
  INVALID_INPUT: "INVALID_INPUT",
  UNKNOWN: "UNKNOWN",
} as const;

export type ErrorCode = (typeof ERROR_CODES)[keyof typeof ERROR_CODES];

/** 结构化应用错误 */
export class AppError extends Error {
  public readonly code: ErrorCode;
  public readonly isOperational: boolean;

  constructor(message: string, code: ErrorCode = ERROR_CODES.UNKNOWN, isOperational = true) {
    super(message);
    this.name = "AppError";
    this.code = code;
    this.isOperational = isOperational;
    Error.captureStackTrace(this, this.constructor);
  }
}
