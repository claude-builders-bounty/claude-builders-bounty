import { useCallback } from "react";
import type { PetApi } from "@shared/preload-types";
import type { ChatMessage, SystemStats, Reminder } from "@shared/ipc";

import { usePetStore } from "../store/petStore";
import type { PetStoreType } from "../store/petStore";

/**
 * 封装 window.__PET_API__ 调用的基础 hook。
 *
 * 渲染进程严格遵循 Electron 安全边界：所有与主进程的通信
 * 必须经由 preload 脚本暴露的 __PET_API__，绝不直接 require electron。
 *
 * 返回：
 *  - invoke(channel, payload?)：发送 IPC 请求并等待响应（类型化）
 *  - on<T>(channel, callback)：订阅主进程推送的事件，返回取消订阅函数
 *  - off(channel)：移除指定通道的所有监听器（必要时手动清理）
 */
export function usePetApi() {
  const api = window.__PET_API__ as PetApi | undefined;

  const invoke = useCallback(
    async <T = unknown>(
      channel: keyof PetApi,
      ...args: unknown[]
    ): Promise<T> => {
      if (!api) {
        throw new Error(
          "__PET_API__ 未就绪：渲染进程未注入 preload API"
        );
      }
      const method = api[channel as keyof PetApi] as (
        ...a: unknown[]
      ) => unknown;
      const result = await method(...args);
      return result as T;
    },
    [api]
  );

  const on = useCallback(
    <T = unknown>(
      channel: "chat:stream" | "monitor:stats" | "app:quit",
      callback: (data: T) => void
    ): (() => void) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const unsubscribe = (api as any).on(
        channel,
        callback as (data: T) => void
      );
      return unsubscribe;
    },
    [api]
  );

  const off = useCallback(() => {
    // contextBridge 的 on 返回取消订阅函数，调用方应自行保管；
    // 此处保留 off 接口以供显式清理（如需可扩展为维护订阅表）
  }, []);

  return { invoke, on, off };
}

/* ------------------------------------------------------------------------
   业务 hooks：基于 zustand store 的便捷封装
   ------------------------------------------------------------------------ */

/** 宠物状态业务 hook */
export function usePetState() {
  const pet = usePetStore((s: PetStoreType) => s.pet);
  const setPetState = usePetStore((s: PetStoreType) => s.setPetState);
  const setPetMood = usePetStore((s: PetStoreType) => s.setPetMood);
  const playPetAnimation = usePetStore((s: PetStoreType) => s.playPetAnimation);
  const setAffection = usePetStore((s: PetStoreType) => s.setAffection);
  const fetchPetState = usePetStore((s: PetStoreType) => s.fetchPetState);
  const fetchAffection = usePetStore((s: PetStoreType) => s.fetchAffection);

  return {
    ...pet,
    setPetState,
    setPetMood,
    playPetAnimation,
    setAffection,
    fetchPetState,
    fetchAffection,
  };
}

/** 聊天业务 hook */
export function useChat() {
  const chat = usePetStore((s: PetStoreType) => s.chat);
  const sendMessage = usePetStore((s: PetStoreType) => s.sendMessage);
  const fetchChatHistory = usePetStore((s: PetStoreType) => s.fetchChatHistory);
  const clearChatHistory = usePetStore((s: PetStoreType) => s.clearChatHistory);
  const appendStreamChunk = usePetStore((s: PetStoreType) => s.appendStreamChunk);
  const setStreaming = usePetStore((s: PetStoreType) => s.setStreaming);

  return {
    ...chat,
    sendMessage,
    fetchChatHistory,
    clearChatHistory,
    appendStreamChunk,
    setStreaming,
  };
}

/** 设置业务 hook */
export function useSettings() {
  const settings = usePetStore((s: PetStoreType) => s.settings);
  const fetchSettings = usePetStore((s: PetStoreType) => s.fetchSettings);
  const fetchLlmConfig = usePetStore((s: PetStoreType) => s.fetchLlmConfig);
  const setSettings = usePetStore((s: PetStoreType) => s.setSettings);
  const setLlmConfig = usePetStore((s: PetStoreType) => s.setLlmConfig);

  return {
    ...settings,
    fetchSettings,
    fetchLlmConfig,
    setSettings,
    setLlmConfig,
  };
}

/** 系统监控业务 hook */
export function useMonitor() {
  const system = usePetStore((s: PetStoreType) => s.system);
  const startMonitor = usePetStore((s: PetStoreType) => s.startMonitor);
  const stopMonitor = usePetStore((s: PetStoreType) => s.stopMonitor);
  const setStats = usePetStore((s: PetStoreType) => s.setStats);

  return {
    ...system,
    startMonitor,
    stopMonitor,
    setStats,
  };
}

/** 提醒业务 hook */
export function useReminders() {
  const settings = usePetStore((s: PetStoreType) => s.settings);
  const fetchReminders = usePetStore((s: PetStoreType) => s.fetchReminders);
  const addReminder = usePetStore((s: PetStoreType) => s.addReminder);
  const removeReminder = usePetStore((s: PetStoreType) => s.removeReminder);
  const toggleReminder = usePetStore((s: PetStoreType) => s.toggleReminder);

  return {
    reminders: settings.reminders,
    fetchReminders,
    addReminder,
    removeReminder,
    toggleReminder,
  };
}

/** 窗口控制业务 hook */
export function useWindow() {
  const clickThrough = usePetStore((s: PetStoreType) => s.clickThrough);
  const alwaysOnTop = usePetStore((s: PetStoreType) => s.alwaysOnTop);
  const setClickThrough = usePetStore((s: PetStoreType) => s.setClickThrough);
  const setAlwaysOnTop = usePetStore((s: PetStoreType) => s.setAlwaysOnTop);
  const toggleDevTools = usePetStore((s: PetStoreType) => s.toggleDevTools);
  const closeWindow = usePetStore((s: PetStoreType) => s.closeWindow);
  const minimizeWindow = usePetStore((s: PetStoreType) => s.minimizeWindow);
  const dragWindow = usePetStore((s: PetStoreType) => s.dragWindow);

  return {
    clickThrough,
    alwaysOnTop,
    setClickThrough,
    setAlwaysOnTop,
    toggleDevTools,
    closeWindow,
    minimizeWindow,
    dragWindow,
  };
}

export type { PetApi, ChatMessage, SystemStats, Reminder };
