import { create, type StoreApi, type UseBoundStore } from "zustand";
import type { PetApi } from "../../shared/preload-types";
import type {
  PetState,
  PetMood,
  PetAnimation,
  ChatMessage,
  AppSettings,
  LlmConfig,
  Reminder,
  SystemStats,
} from "../../shared/ipc";

/* ========================================================================
   Slice 类型定义
   ======================================================================== */

/** 宠物状态 slice */
export interface PetSlice {
  pet: {
    state: PetState | null;
    affection: number;
  };
  setPetState: (state: Partial<PetState>) => Promise<void>;
  setPetMood: (mood: PetMood) => Promise<void>;
  playPetAnimation: (animation: PetAnimation) => Promise<void>;
  setAffection: (value: number) => Promise<void>;
  fetchPetState: () => Promise<void>;
  fetchAffection: () => Promise<void>;
}

/** 聊天 slice */
export interface ChatSlice {
  chat: {
    messages: ChatMessage[];
    isStreaming: boolean;
    streamBuffer: string;
  };
  sendMessage: (content: string) => Promise<void>;
  fetchChatHistory: () => Promise<void>;
  clearChatHistory: () => Promise<void>;
  appendStreamChunk: (chunk: string) => void;
  setStreaming: (streaming: boolean) => void;
}

/** 设置 slice */
export interface SettingsSlice {
  settings: AppSettings;
  fetchSettings: () => Promise<void>;
  fetchLlmConfig: () => Promise<void>;
  setSettings: (settings: Partial<AppSettings>) => Promise<void>;
  setLlmConfig: (config: Partial<LlmConfig>) => Promise<void>;
}

/** 系统监控 slice */
export interface SystemSlice {
  system: {
    stats: SystemStats | null;
    monitorActive: boolean;
  };
  startMonitor: () => Promise<void>;
  stopMonitor: () => Promise<void>;
  setStats: (stats: SystemStats) => void;
}

/** 提醒 slice */
export interface ReminderSlice {
  fetchReminders: () => Promise<void>;
  addReminder: (
    reminder: Omit<Reminder, "id" | "createdAt">
  ) => Promise<Reminder>;
  removeReminder: (id: string) => Promise<void>;
  toggleReminder: (id: string) => Promise<void>;
}

/** 窗口 slice */
export interface WindowSlice {
  clickThrough: boolean;
  alwaysOnTop: boolean;
  setClickThrough: (enabled: boolean) => Promise<void>;
  setAlwaysOnTop: (enabled: boolean) => Promise<void>;
  toggleDevTools: () => Promise<void>;
  closeWindow: () => Promise<void>;
  minimizeWindow: () => Promise<void>;
  dragWindow: () => Promise<void>;
}

/** 完整 store 类型 */
export type PetStore = PetSlice &
  ChatSlice &
  SettingsSlice &
  SystemSlice &
  ReminderSlice &
  WindowSlice;

/** 用于 hooks selector 的 store 类型别名 */
export type PetStoreType = PetStore;

/* ========================================================================
   Store 工厂：接受 PetApi 实例，返回 zustand store。
   api 可为 undefined（仅在非浏览器/未注入时），actions 内部会校验。
   ======================================================================== */

export function createPetStore(api?: PetApi): UseBoundStore<StoreApi<PetStore>> {
  return create<PetStore>((set) => ({
    /* ---------- Pet ---------- */
    pet: { state: null, affection: 0 },

    setPetState: async (partial) => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      await api.setPetState(partial);
      set((s) => ({
        pet: {
          ...s.pet,
          state: s.pet.state ? { ...s.pet.state, ...partial } : null,
        },
      }));
    },

    setPetMood: async (mood) => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      await api.setPetMood(mood);
      set((s) => ({
        pet: {
          ...s.pet,
          state: s.pet.state ? { ...s.pet.state, mood } : null,
        },
      }));
    },

    playPetAnimation: async (animation) => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      await api.playPetAnimation(animation);
      set((s) => ({
        pet: {
          ...s.pet,
          state: s.pet.state ? { ...s.pet.state, animation } : null,
        },
      }));
    },

    setAffection: async (value) => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      await api.setAffection(value);
      set((s) => ({ pet: { ...s.pet, affection: value } }));
    },

    fetchPetState: async () => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      const state = await api.getPetState();
      set((s) => ({ pet: { ...s.pet, state } }));
      set((s) => ({ pet: { ...s.pet, affection: state.affection } }));
    },

    fetchAffection: async () => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      const affection = await api.getAffection();
      set((s) => ({ pet: { ...s.pet, affection } }));
    },

    /* ---------- Chat ---------- */
    chat: { messages: [], isStreaming: false, streamBuffer: "" },

    sendMessage: async (content) => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      const { content: reply, animation, mood } = await api.sendMessage(content);
      const now = Date.now();
      set((s) => ({
        chat: {
          ...s.chat,
          streamBuffer: "",
          messages: [
            ...s.chat.messages,
            { role: "user", content, timestamp: now, id: `user-${now}` },
            {
              role: "assistant",
              content: reply,
              timestamp: now + 1,
              id: `assistant-${now + 1}`,
              animation,
              mood,
            },
          ],
        },
      }));
      if (animation) await api.playPetAnimation(animation);
      if (mood) await api.setPetMood(mood);
    },

    fetchChatHistory: async () => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      const messages = await api.getChatHistory();
      set((s) => ({ chat: { ...s.chat, messages } }));
    },

    clearChatHistory: async () => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      await api.clearChatHistory();
      set((s) => ({ chat: { ...s.chat, messages: [] } }));
    },

    appendStreamChunk: (chunk) => {
      set((s) => ({
        chat: { ...s.chat, streamBuffer: s.chat.streamBuffer + chunk },
      }));
    },

    setStreaming: (streaming) => {
      set((s) => ({ chat: { ...s.chat, isStreaming: streaming } }));
    },

    /* ---------- Settings ---------- */
    settings: {
      llm: {
        provider: "openai",
        apiKey: "",
        baseUrl: "https://api.openai.com/v1",
        model: "gpt-4o-mini",
        temperature: 0.8,
        maxTokens: 1000,
        systemPrompt: "",
      },
      showMonitor: false,
      monitorInterval: 5000,
      reminders: [],
      clickThrough: false,
      alwaysOnTop: true,
      autoStart: false,
      language: "zh-CN",
    },

    fetchSettings: async () => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      const settings = await api.getSettings();
      set((s) => ({
        settings: {
          ...s.settings,
          llm: settings.llm,
          showMonitor: settings.showMonitor,
          reminders: settings.reminders,
        },
      }));
    },

    fetchLlmConfig: async () => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      const llm = await api.getLlmConfig();
      set((s) => ({ settings: { ...s.settings, llm } }));
    },

    setSettings: async (partial) => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      await api.setSettings(partial);
      set((s) => ({ settings: { ...s.settings, ...partial } }));
    },

    setLlmConfig: async (config) => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      await api.setLlmConfig(config);
      set((s) => ({
        settings: {
          ...s.settings,
          llm: { ...s.settings.llm, ...config } as LlmConfig,
        },
      }));
    },

    /* ---------- System ---------- */
    system: { stats: null, monitorActive: false },

    startMonitor: async () => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      await api.startMonitor();
      set((s) => ({ system: { ...s.system, monitorActive: true } }));
    },

    stopMonitor: async () => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      await api.stopMonitor();
      set((s) => ({ system: { ...s.system, monitorActive: false } }));
    },

    setStats: (stats) => {
      set((s) => ({ system: { ...s.system, stats } }));
    },

    /* ---------- Reminder ---------- */
    fetchReminders: async () => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      const reminders = await api.getReminders();
      set((s) => ({ settings: { ...s.settings, reminders } }));
    },

    addReminder: async (reminder) => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      const created = await api.addReminder(reminder);
      set((s) => ({
        settings: {
          ...s.settings,
          reminders: [...s.settings.reminders, created],
        },
      }));
      return created;
    },

    removeReminder: async (id) => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      await api.removeReminder(id);
      set((s) => ({
        settings: {
          ...s.settings,
          reminders: s.settings.reminders.filter((r) => r.id !== id),
        },
      }));
    },

    toggleReminder: async (id) => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      await api.toggleReminder(id);
      set((s) => ({
        settings: {
          ...s.settings,
          reminders: s.settings.reminders.map((r) =>
            r.id === id ? { ...r, enabled: !r.enabled } : r
          ),
        },
      }));
    },

    /* ---------- Window ---------- */
    clickThrough: false,
    alwaysOnTop: false,

    setClickThrough: async (enabled) => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      await api.setClickThrough(enabled);
      set({ clickThrough: enabled });
    },

    setAlwaysOnTop: async (enabled) => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      await api.setAlwaysOnTop(enabled);
      set({ alwaysOnTop: enabled });
    },

    toggleDevTools: async () => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      await api.toggleDevTools();
    },

    closeWindow: async () => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      await api.closeWindow();
    },

    minimizeWindow: async () => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      await api.minimizeWindow();
    },

    dragWindow: async () => {
      if (!api) throw new Error("__PET_API__ 未就绪");
      await api.dragWindow();
    },
  }));
}

/* ========================================================================
   默认 store：基于 preload 注入的 window.__PET_API__
   ======================================================================== */

export const usePetStore = createPetStore(
  typeof window !== "undefined" ? (window.__PET_API__ as PetApi) : undefined
);
