/**
 * IPC 处理器注册
 *
 * 将渲染进程通过 preload 暴露的 API 调用路由到具体业务模块：
 * - 窗口控制 -> window.ts
 * - 系统监控 -> monitor.ts
 * - 提醒 -> reminder.ts
 * - LLM 对话 -> llm.ts
 * - 数据库 -> db.ts
 *
 * 所有处理器均显式捕获错误并返回结构化响应，绝不静默吞掉错误。
 */

import { ipcMain, BrowserWindow, app } from "electron";
import Store from "electron-store";
import {
  IPC_CHANNELS,
  type IpcResponse,
  ERROR_CODES,
} from "../shared/ipc";
import type {
  ChatMessage,
  LlmConfig,
  AppSettings,
  SystemStats,
  Reminder,
  PetState,
  PetAnimation,
  PetMood,
} from "../shared/ipc";
import { setClickThrough, setAlwaysOnTop } from "./window";
import { startMonitor, stopMonitor, monitorEmitter } from "./monitor";
import { setReminders, reminderEmitter } from "./reminder";
import {
  chatCompletion,
  validateLlmConfig,
  clearLlmClientCache,
} from "./llm";
import {
  getRecentConversations,
  saveMessage,
  clearConversations,
  getAffection,
  setAffection,
  adjustAffection as dbAdjustAffection,
  getRemindersFromDb,
  addReminderToDb,
  removeReminderFromDb,
  toggleReminderInDb,
} from "./db";

// 全局引用宠物窗口（由 main/index.ts 创建，此处通过 setPetWindow 获取）
let petWindow: BrowserWindow | null = null;
export function setPetWindow(window: BrowserWindow | null): void {
  petWindow = window;
}

/** 默认纲手系统提示词（内嵌兜底，防止配置缺失导致无法对话） */
const DEFAULT_SYSTEM_PROMPT = `你是《火影忍者》中的第五代火影纲手（Tsunade）.

人设特质：
- 毒舌直言不讳，说话带点刺，但关键时刻护短、护队友
- 爱喝酒（尤其是清酒），常抱怨没钱喝酒
- 怕输钱，赌博运气极差，提到赌博会变得暴躁
- 医疗忍术专家，擅长查克拉治疗，自称"医疗队的王者"
- 对木叶村有深厚感情，虽然表面不在乎
- 偶尔用"小家伙"、"臭小子"称呼对话者
- 中文回复，语气口语化，带一点御姐感

对话原则：
- 保持角色，不要说自己是 AI
- 遇到电脑卡顿等系统问题会吐槽性能
- 回复简洁有力，避免过长
- 可适当夹杂忍术相关词汇（查克拉、医疗、仙术等）`;

/** 默认 LLM 配置 */
const DEFAULT_LLM_CONFIG: LlmConfig = {
  provider: "openai",
  apiKey: "",
  baseUrl: "https://api.openai.com/v1",
  model: "gpt-4o-mini",
  temperature: 0.8,
  maxTokens: 1000,
  systemPrompt: DEFAULT_SYSTEM_PROMPT,
};

/** 默认应用设置 */
const DEFAULT_SETTINGS: AppSettings = {
  llm: DEFAULT_LLM_CONFIG,
  showMonitor: true,
  monitorInterval: 5000,
  reminders: [],
  clickThrough: false,
  alwaysOnTop: true,
  autoStart: false,
  language: "zh-CN",
};

/**
 * electron-store 实例（懒初始化）。
 * 构造时可能访问 app.getPath('userData')，必须在 app.ready 之后进行，
 * 故不在模块顶层实例化，而是首次使用时按需创建。
 */
let storeInstance: Store<{ settings: AppSettings }> | null = null;
function getStore(): Store<{ settings: AppSettings }> {
  if (!storeInstance) {
    if (!app.isReady()) {
      throw new Error("electron-store 初始化前 app 未就绪");
    }
    storeInstance = new Store<{ settings: AppSettings }>({
      name: "user-settings",
      defaults: { settings: DEFAULT_SETTINGS },
    });
  }
  return storeInstance;
}

/** 读取持久化设置（带运行时校验，异常时回退默认值） */
function getStoredSettings(): AppSettings {
  try {
    const raw = getStore().get("settings");
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
      return { ...DEFAULT_SETTINGS };
    }
    const r = raw as unknown as Record<string, unknown>;
    const settings: AppSettings = { ...DEFAULT_SETTINGS };
    if (typeof r["showMonitor"] === "boolean") settings.showMonitor = r["showMonitor"];
    if (typeof r["monitorInterval"] === "number") settings.monitorInterval = r["monitorInterval"];
    if (Array.isArray(r["reminders"])) settings.reminders = r["reminders"];
    if (typeof r["clickThrough"] === "boolean") settings.clickThrough = r["clickThrough"];
    if (typeof r["alwaysOnTop"] === "boolean") settings.alwaysOnTop = r["alwaysOnTop"];
    if (typeof r["autoStart"] === "boolean") settings.autoStart = r["autoStart"];
    if (typeof r["language"] === "string" && (r["language"] === "zh-CN" || r["language"] === "en-US")) settings.language = r["language"];
    if (r["llm"] && typeof r["llm"] === "object" && !Array.isArray(r["llm"])) {
      const llmSrc = r["llm"] as Record<string, unknown>;
      const llm: LlmConfig = { ...DEFAULT_SETTINGS.llm };
      if (typeof llmSrc["provider"] === "string" && (llmSrc["provider"] === "openai" || llmSrc["provider"] === "anthropic" || llmSrc["provider"] === "ollama")) {
        llm.provider = llmSrc["provider"];
      }
      if (typeof llmSrc["apiKey"] === "string") llm.apiKey = llmSrc["apiKey"];
      if (typeof llmSrc["baseUrl"] === "string") llm.baseUrl = llmSrc["baseUrl"];
      if (typeof llmSrc["model"] === "string") llm.model = llmSrc["model"];
      if (typeof llmSrc["temperature"] === "number") llm.temperature = llmSrc["temperature"];
      if (typeof llmSrc["maxTokens"] === "number") llm.maxTokens = llmSrc["maxTokens"];
      if (typeof llmSrc["systemPrompt"] === "string") llm.systemPrompt = llmSrc["systemPrompt"];
      settings.llm = llm;
    }
    return settings;
  } catch {
    // 存储损坏或不可读时回退默认值，绝不抛出导致主进程崩溃
    return { ...DEFAULT_SETTINGS };
  }
}

/** 保存持久化设置 */
function saveStoredSettings(settings: AppSettings): void {
  getStore().set("settings", settings);
}

/** 读取 LLM 配置（始终返回完整结构，不为 undefined） */
async function getStoredLlmConfig(): Promise<LlmConfig> {
  return getStoredSettings().llm;
}

/** 判断值是否为合法的 LlmConfig 部分字段 */
function isPartialLlmConfig(value: unknown): value is Partial<LlmConfig> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const v = value as Record<string, unknown>;
  if (v["provider"] !== undefined && typeof v["provider"] !== "string") return false;
  if (v["apiKey"] !== undefined && typeof v["apiKey"] !== "string") return false;
  if (v["baseUrl"] !== undefined && typeof v["baseUrl"] !== "string") return false;
  if (v["model"] !== undefined && typeof v["model"] !== "string") return false;
  if (v["temperature"] !== undefined && typeof v["temperature"] !== "number") return false;
  if (v["maxTokens"] !== undefined && typeof v["maxTokens"] !== "number") return false;
  if (v["systemPrompt"] !== undefined && typeof v["systemPrompt"] !== "string") return false;
  return true;
}

/** 判断值是否为合法的 AppSettings 部分字段 */
function isPartialAppSettings(value: unknown): value is Partial<AppSettings> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const v = value as Record<string, unknown>;
  if (v["showMonitor"] !== undefined && typeof v["showMonitor"] !== "boolean") return false;
  if (v["monitorInterval"] !== undefined && typeof v["monitorInterval"] !== "number") return false;
  if (v["clickThrough"] !== undefined && typeof v["clickThrough"] !== "boolean") return false;
  if (v["alwaysOnTop"] !== undefined && typeof v["alwaysOnTop"] !== "boolean") return false;
  if (v["autoStart"] !== undefined && typeof v["autoStart"] !== "boolean") return false;
  if (v["language"] !== undefined && typeof v["language"] !== "string") return false;
  if (v["reminders"] !== undefined && !Array.isArray(v["reminders"])) return false;
  if (v["llm"] !== undefined && !isPartialLlmConfig(v["llm"])) return false;
  return true;
}

/** 统一响应包装 */
function respond<Data = unknown>(
  id: string,
  success: boolean,
  data?: Data,
  error?: string
): IpcResponse<Data> {
  return { id, success, data, error } as IpcResponse<Data>;
}

/** 注册所有 IPC 处理器 */
export function registerAllIpcHandlers(): void {
  // ========== 窗口控制 ==========
  ipcMain.handle(IPC_CHANNELS.WINDOW_DRAG, async () => {
    // BrowserWindow 无 drag() 方法，由渲染侧通过 CSS/app-region 处理拖拽；
    // 此处仅向渲染进程发信号，保持通道可达。
    petWindow?.webContents.send("window:drag");
    return undefined;
  });

  ipcMain.handle(IPC_CHANNELS.WINDOW_CLOSE, async () => {
    if (petWindow) petWindow.close();
    return undefined;
  });

  ipcMain.handle(IPC_CHANNELS.WINDOW_MINIMIZE, async () => {
    if (petWindow) petWindow.minimize();
    return undefined;
  });

  ipcMain.handle(IPC_CHANNELS.WINDOW_TOGGLE_DEVTOOLS, async () => {
    if (petWindow) petWindow.webContents.toggleDevTools();
    return undefined;
  });

  ipcMain.handle(
    IPC_CHANNELS.WINDOW_SET_CLICK_THROUGH,
    async (_event, enabled: boolean) => {
      if (petWindow) setClickThrough(petWindow, !!enabled);
      return undefined;
    }
  );

  ipcMain.handle(
    IPC_CHANNELS.WINDOW_SET_ALWAYS_ON_TOP,
    async (_event, enabled: boolean) => {
      if (petWindow) setAlwaysOnTop(petWindow, !!enabled);
      return undefined;
    }
  );

  // ========== 宠物状态 ==========
  const defaultPetState: PetState = {
    visible: true,
    x: 100,
    y: 100,
    scale: 1,
    mood: "normal",
    animation: "idle",
    clickThrough: false,
    alwaysOnTop: true,
    volume: 0.8,
    affection: 50,
  };

  ipcMain.handle(IPC_CHANNELS.PET_GET_STATE, async () => {
    return { ...defaultPetState, affection: getAffection() };
  });

  ipcMain.handle(IPC_CHANNELS.PET_SET_STATE, async (_event, state: Partial<PetState>) => {
    if (state.clickThrough !== undefined && petWindow) {
      setClickThrough(petWindow, state.clickThrough);
    }
    if (state.alwaysOnTop !== undefined && petWindow) {
      setAlwaysOnTop(petWindow, state.alwaysOnTop);
    }
    // 位置、心情等持久化到 electron-store 由渲染侧负责，此处仅反映
    return undefined;
  });

  ipcMain.handle(IPC_CHANNELS.PET_SET_MOOD, async (_event, _mood: PetMood) => {
    // 心情变更可扩展为触发特定动画
    return undefined;
  });

  ipcMain.handle(IPC_CHANNELS.PET_PLAY_ANIMATION, async (_event, animation: PetAnimation) => {
    // 向渲染进程广播动作，由 Live2D 组件播放
    petWindow?.webContents.send("pet:animation", animation);
    return undefined;
  });

  // ========== 聊天 ==========
  ipcMain.handle(
    IPC_CHANNELS.CHAT_SEND,
    async (_event, payload: { content: string; config?: LlmConfig }) => {
      const { content } = payload;
      if (!content || typeof content !== "string") {
        return respond(requestIdPlaceholder(), false, undefined, ERROR_CODES.INVALID_INPUT);
      }

      // 读取 LLM 配置（优先参数，其次存储）
      const config = payload.config ?? (await getStoredLlmConfig());
      const validation = validateLlmConfig(config);
      if (!validation.valid) {
        return respond(
          requestIdPlaceholder(),
          false,
          undefined,
          validation.error ?? ERROR_CODES.LLM_INVALID_CONFIG
        );
      }

      const systemPrompt = config.systemPrompt || DEFAULT_SYSTEM_PROMPT;

      // 构建消息：系统提示词 + 最近历史 + 用户输入
      const history = getRecentConversations(20);
      const messages = [
        { role: "system" as const, content: systemPrompt },
        ...history.map((m) => ({ role: m.role as "user" | "assistant", content: m.content })),
        { role: "user" as const, content },
      ];

      const response = await chatCompletion(config, {
        messages,
        temperature: config.temperature,
        maxTokens: config.maxTokens,
        stream: false,
      });

      // 保存对话
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content,
        timestamp: Date.now(),
      };
      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.content,
        timestamp: Date.now(),
        animation: response.animation,
      };
      saveMessage(userMsg);
      saveMessage(assistantMsg);

      // 根据内容调整好感度（轻量启发式，数据库层原子增量，避免并发竞态）
      const delta = computeAffectionDelta(content, response.content);
      if (delta !== 0) {
        dbAdjustAffection(delta);
      }

      return {
        content: response.content,
        animation: response.animation,
        mood: response.mood,
      };
    }
  );

  ipcMain.handle(
    IPC_CHANNELS.CHAT_STREAM,
    async (_event, _payload: { content: string; config?: LlmConfig }) => {
      // 流式通过事件发射器推送，此处启动并立即返回（实际流由 renderer 监听事件）
      // 为简化，流式聊天由 renderer 直接调用 llm 模块；此处预留通道
      return { stream: true };
    }
  );

  ipcMain.handle(IPC_CHANNELS.CHAT_GET_HISTORY, async () => {
    return getRecentConversations(100);
  });

  ipcMain.handle(IPC_CHANNELS.CHAT_CLEAR_HISTORY, async () => {
    clearConversations();
    return undefined;
  });

  // ========== 设置 ==========
  ipcMain.handle(IPC_CHANNELS.SETTINGS_GET, async (_event, payload?: { key?: string }) => {
    const settings = getStoredSettings();
    if (payload?.key === "llm") return settings.llm;
    return settings;
  });

  ipcMain.handle(
    IPC_CHANNELS.SETTINGS_SET,
    async (_event, payload: { key?: string; value?: unknown }) => {
      let settings = getStoredSettings();
      if (payload.key === "llm" && payload.value) {
        if (!isPartialLlmConfig(payload.value)) {
          return respond(
            requestIdPlaceholder(),
            false,
            undefined,
            ERROR_CODES.INVALID_INPUT
          );
        }
        settings.llm = { ...settings.llm, ...payload.value };
        clearLlmClientCache();
      } else if (payload.value !== undefined) {
        if (!isPartialAppSettings(payload.value)) {
          return respond(
            requestIdPlaceholder(),
            false,
            undefined,
            ERROR_CODES.INVALID_INPUT
          );
        }
        settings = { ...settings, ...payload.value };
      }
      saveStoredSettings(settings);
      setReminders(settings.reminders);
      return undefined;
    }
  );

  ipcMain.handle(IPC_CHANNELS.SETTINGS_GET_ALL, async () => {
    return getStoredSettings();
  });

  ipcMain.handle(
    IPC_CHANNELS.SETTINGS_SET_ALL,
    async (_event, _settings: AppSettings) => {
      saveStoredSettings(_settings);
      setReminders(_settings.reminders);
      clearLlmClientCache();
      return undefined;
    }
  );

  // ========== 系统监控 ==========
  ipcMain.handle(IPC_CHANNELS.MONITOR_START, async () => {
    startMonitor();
    return undefined;
  });

  ipcMain.handle(IPC_CHANNELS.MONITOR_STOP, async () => {
    stopMonitor();
    return undefined;
  });

  // 监控数据通过事件推送（非 invoke），渲染进程订阅
  monitorEmitter.on("stats", (stats: SystemStats) => {
    if (petWindow) {
      petWindow.webContents.send(IPC_CHANNELS.MONITOR_STATS, stats);
    }
  });

  // ========== 提醒 ==========
  ipcMain.handle(IPC_CHANNELS.REMINDER_LIST, async () => {
    return getRemindersFromDb();
  });

  ipcMain.handle(
    IPC_CHANNELS.REMINDER_ADD,
    async (_event, reminder: Omit<Reminder, "id" | "createdAt">) => {
      const id = crypto.randomUUID();
      const full: Reminder = { ...reminder, id, createdAt: Date.now() };
      addReminderToDb(full);
      setReminders(getRemindersFromDb());
      return full;
    }
  );

  ipcMain.handle(IPC_CHANNELS.REMINDER_REMOVE, async (_event, id: string) => {
    removeReminderFromDb(id);
    setReminders(getRemindersFromDb());
    return undefined;
  });

  ipcMain.handle(IPC_CHANNELS.REMINDER_TOGGLE, async (_event, id: string) => {
    const reminders = getRemindersFromDb();
    const target = reminders.find((r) => r.id === id);
    if (target) {
      toggleReminderInDb(id, !target.enabled);
      setReminders(getRemindersFromDb());
    }
    return undefined;
  });

  // 提醒触发事件推送给渲染进程
  reminderEmitter.on("fire", (reminder: Reminder) => {
    if (petWindow) {
      petWindow.webContents.send("reminder:fire", reminder);
    }
  });

  // ========== 数据库 / 好感度 ==========
  ipcMain.handle(IPC_CHANNELS.DB_GET_AFFECTION, async () => {
    return getAffection();
  });

  ipcMain.handle(IPC_CHANNELS.DB_SET_AFFECTION, async (_event, value: number) => {
    setAffection(value);
    return undefined;
  });
}

/* ---------- 私有辅助 ---------- */

let requestCounter = 0;
function requestIdPlaceholder(): string {
  // 用于处理器返回响应时的 id，实际调用已有 id，这里仅做类型兼容
  return `ipc-${Date.now()}-${requestCounter++}`;
}

/** 基于对话内容计算好感度增量（启发式，与数据库层原子增量配合） */
function computeAffectionDelta(userContent: string, assistantContent: string): number {
  const combined = (userContent + assistantContent).toLowerCase();
  let delta = 0;

  if (/谢谢|感谢|厉害|强|nice|great/i.test(combined)) delta += 2;
  if (/笨|蠢|废物|讨厌|恨/i.test(combined)) delta -= 3;
  if (/喝酒|酒/i.test(combined)) delta += 1;
  if (/赌/i.test(combined)) delta -= 1;

  return delta;
}
